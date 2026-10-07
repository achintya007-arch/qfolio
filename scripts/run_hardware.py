"""Run simulator-trained XY-QAOA on IBM Quantum hardware (docs/06_HARDWARE_RUNBOOK.md).

Usage:
    python scripts/run_hardware.py --dry-run                   # FakeTorino, same SamplerV2 path
    python scripts/run_hardware.py --submit [--backend ibm_torino]
    python scripts/run_hardware.py --status
    python scripts/run_hardware.py --collect

The IBM token must already be saved with ``QiskitRuntimeService.save_account``; this script
never reads, prints or asks for it.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qportfolio import hardware as hw
from qportfolio.circuits import build_qaoa
from qportfolio.config import load_config
from qportfolio.data import load_prices, returns_stats
from qportfolio.io import save_result
from qportfolio.problem import PortfolioProblem
from qportfolio.qaoa import optimize

OUTDIR = Path("results/hardware")


def hardware_problem(cfg: dict[str, Any]) -> PortfolioProblem:
    """The 4-asset, k=2 instance from ``hardware_problem`` in the config."""
    d, hp = cfg["data"], cfg["hardware_problem"]
    mu, sigma = returns_stats(load_prices(d["path"], hp["tickers"], d["start"], d["end"]))
    labels = tuple(t.removesuffix(".NS") for t in hp["tickers"])
    return PortfolioProblem(mu, sigma, k=hp["k"], q=hp["q"], labels=labels)


def print_gap(p: PortfolioProblem, gap: dict[str, Any]) -> None:
    """Show how close the best two baskets are (small gap = noise can swap them)."""
    print(f"Instance: {', '.join(p.labels)}  (n = {p.n}, k = {p.k}, q = {p.q})")
    print(f"  best   {gap['best_bits']}  cost {gap['best_cost']:.4f}")
    print(f"  second {gap['second_bits']}  cost {gap['second_cost']:.4f}")
    rel = gap["gap"] / gap["cost_range"]
    print(f"  cost gap best→second = {gap['gap']:.4f}  ({rel:.1%} of the feasible cost range)\n")


def prepare(cfg: Any, backend_name: str | None, dry_run: bool) -> tuple[Any, list, dict]:
    """Train angles on the statevector simulator, transpile, and build the job metadata."""
    raw, hcfg, q = cfg.raw, cfg.raw["hardware"], cfg.raw["qaoa"]
    p = hardware_problem(raw)
    gap = hw.cost_gap(p)
    print_gap(p, gap)

    circuits, params = [], {}
    for reps in hcfg["reps"]:
        ansatz, H = build_qaoa(p, reps=reps, variant="xy")
        res = optimize(ansatz, H, restarts=q["restarts"], maxiter=q["maxiter"], seed=cfg.seed)
        print(f"Trained XY-QAOA p={reps} on statevector: ⟨H⟩ = {res.energy:.4f}")
        circ = ansatz.assign_parameters(res.params)
        circ.measure_all()
        circuits.append(circ)
        params[str(reps)] = res.params.tolist()

    backend = hw.get_backend(backend_name, dry_run)
    isa, layouts, physical = hw.transpile_pubs(circuits, backend, seed=cfg.seed)
    meta = {
        "backend": backend.name,
        "dry_run": dry_run,
        "shots": hcfg["shots"],
        "reps": hcfg["reps"],
        "params": params,  # QAOAAnsatz order: all β, then all γ
        "layouts": layouts,
        "calibrated_qubits": physical,
        "transpiled": [hw.circuit_stats(tc) for tc in isa],
        "backend_snapshot": hw.backend_snapshot(backend, physical),
        "options": {
            "dynamical_decoupling": hcfg["dynamical_decoupling"],
            "twirling": hcfg["twirling"],
        },
        "instance": {"tickers": list(p.labels), "k": p.k, "q": p.q, **gap},
    }
    for reps, lay, st in zip(hcfg["reps"], layouts, meta["transpiled"], strict=False):
        print(
            f"p={reps}: physical qubits {lay}, "
            f"depth {st['depth']}, {st['two_qubit_gates']} 2q gates"
        )
    sampler = hw.configure_sampler(
        backend, hcfg["shots"], cfg.seed, hcfg["dynamical_decoupling"], hcfg["twirling"]
    )
    return sampler, isa, meta


def report(p: PortfolioProblem, record: dict[str, Any]) -> None:
    """Print raw / post-selected / mitigated metrics per depth."""
    print(
        f"\n{'run':<16} {'P(feas)':>8} {'P(opt)':>8} {'P(top2)':>8} {'AR':>6}"
        f"  (random {record['p_random']:.3f})"
    )
    for run in record["runs"]:
        for kind in ("raw", "postselected", "mitigated"):
            m = run[kind]
            if m is None:
                continue
            name = f"p={run['reps']} {kind}"
            print(
                f"{name:<16} {m['p_feasible']:>8.3f} {m['p_optimal']:>8.3f} "
                f"{m['p_top2']:>8.3f} {m['approx_ratio']:>6.3f}"
            )


def counts_per_pub(result: Any) -> list[dict[str, int]]:
    """Counts dict for every PUB (QAOA circuits, then cal_0, cal_1)."""
    return [pub.data.meas.get_counts() for pub in result]


def cmd_dry_run(cfg: Any, outdir: Path) -> Path:
    """Submit to FakeTorino through SamplerV2, wait, and score exactly like ``--collect``."""
    sampler, isa, meta = prepare(cfg, None, dry_run=True)
    job = sampler.run(isa)
    record = hw.summarise(hardware_problem(cfg.raw), counts_per_pub(job.result()), meta)
    record = {**meta, **record, "job_id": f"dry-run-{job.job_id()}"}
    report(hardware_problem(cfg.raw), record)
    path = save_result(record, outdir / f"dry_run_{meta['backend']}.json")
    print(f"\nDry run OK → {path}")
    return path


def cmd_submit(cfg: Any, backend_name: str | None, outdir: Path) -> None:
    """Submit one job to real hardware and write ``pending.json``; does not wait."""
    sampler, isa, meta = prepare(cfg, backend_name, dry_run=False)
    job = sampler.run(isa)
    meta = {**meta, "job_id": job.job_id(), "submitted_at": datetime.now(UTC).isoformat()}
    path = save_result(meta, outdir / "pending.json")
    print(f"\nSubmitted job {meta['job_id']} to {meta['backend']} → {path}")


def load_pending(outdir: Path) -> dict[str, Any]:
    """Read the metadata written by ``--submit``."""
    path = outdir / "pending.json"
    if not path.exists():
        sys.exit(f"No {path}; run --submit first.")
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_status(outdir: Path) -> None:
    """Print the queue status of the pending job, and the error message if it failed."""
    meta = load_pending(outdir)
    job = hw.fetch_job(meta["job_id"])
    status = str(job.status())
    print(f"Job {meta['job_id']} on {meta['backend']}: {status}")
    if status == "ERROR":
        print(f"  error: {job.error_message()}")


def cmd_collect(cfg: Any, outdir: Path) -> None:
    """Fetch the finished job, score it and write ``<job_id>.json`` as evidence."""
    meta = load_pending(outdir)
    job = hw.fetch_job(meta["job_id"])
    status = str(job.status())
    if status != "DONE":
        sys.exit(f"Job {meta['job_id']} is {status}; try again later.")
    record = hw.summarise(hardware_problem(cfg.raw), counts_per_pub(job.result()), meta)
    try:
        job_metrics = job.metrics()  # timestamps (created / running / finished) and QPU usage
        record["timestamps"] = job_metrics.get("timestamps")
        record["usage"] = job_metrics.get("usage")
    except Exception as exc:  # metrics are nice-to-have evidence, never block the collect
        record["timestamps"] = {"error": type(exc).__name__}
    record = {**meta, **record}
    report(hardware_problem(cfg.raw), record)
    path = save_result(record, outdir / f"{meta['job_id']}.json")
    print(f"\nCollected → {path}")


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and run one action."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 cannot print ⟨H⟩ / →
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true", help="run on FakeTorino locally")
    action.add_argument("--submit", action="store_true", help="submit to IBM hardware")
    action.add_argument("--status", action="store_true", help="queue status of pending job")
    action.add_argument("--collect", action="store_true", help="fetch and score finished job")
    ap.add_argument(
        "--backend", default=None, help="e.g. ibm_torino (default: config / least busy)"
    )
    ap.add_argument("--outdir", type=Path, default=OUTDIR)
    args = ap.parse_args(argv)

    cfg = load_config()
    if args.dry_run:
        cmd_dry_run(cfg, args.outdir)
    elif args.submit:
        cmd_submit(cfg, args.backend or cfg.raw["hardware"]["backend"], args.outdir)
    elif args.status:
        cmd_status(args.outdir)
    else:
        cmd_collect(cfg, args.outdir)


if __name__ == "__main__":
    main()
