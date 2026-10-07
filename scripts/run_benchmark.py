"""Multi-instance benchmark → ``results/benchmark.json`` (docs/05_BENCHMARK_PROTOCOL.md).

Instance 0 is the headline real-data instance (config ``data.tickers``, ``problem.k/q``);
instances 1..N are the robustness set (random 6-subsets of the 10-ticker universe × q values).
``summary`` is mean ± std over the robustness set only; the headline is reported on its own.

    .venv\\Scripts\\python scripts/run_benchmark.py            # full (~10 min on 10 workers)
    $env:QFOLIO_FAST="1"; .venv\\Scripts\\python scripts/run_benchmark.py   # CI-sized
"""

from __future__ import annotations

import os

# One BLAS thread per worker process: we parallelise over instances instead.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

from qportfolio.benchmark import gap_stats, robustness_specs, run_instance, summarise  # noqa: E402
from qportfolio.config import is_fast_mode, load_config  # noqa: E402
from qportfolio.data import load_prices, returns_stats  # noqa: E402
from qportfolio.io import save_result  # noqa: E402
from qportfolio.problem import PortfolioProblem  # noqa: E402


def make_problem(cfg: dict[str, Any], tickers: tuple[str, ...], k: int, q: float):
    """Build a ``PortfolioProblem`` from the cached prices for these tickers."""
    d = cfg["data"]
    mu, sigma = returns_stats(load_prices(d["path"], list(tickers), d["start"], d["end"]))
    labels = tuple(t.removesuffix(".NS") for t in tickers)
    return PortfolioProblem(mu, sigma, k=k, q=q, labels=labels)


def _run(job: tuple[int, str, tuple[str, ...], int, float, dict, int, dict]) -> dict[str, Any]:
    """Worker: one instance end to end (top-level so Windows ``spawn`` can pickle it)."""
    idx, kind, tickers, k, q, settings, seed, cfg = job
    t0 = time.perf_counter()
    p = make_problem(cfg, tickers, k, q)
    res = run_instance(p, settings, seed, keep_counts=(kind == "headline"))
    print(
        f"  instance {idx:2d} ({kind}, q={q}) done in {time.perf_counter() - t0:.0f} s", flush=True
    )
    return {"id": idx, "kind": kind, "tickers": list(tickers), "seed": seed, **res}


def main() -> None:
    """Run the benchmark and write the results JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/benchmark.json")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    args = ap.parse_args()

    cfg = load_config()
    raw = cfg.raw
    q_cfg, b, c = raw["qaoa"], raw["benchmark"], raw["classical"]
    settings = {
        "restarts": q_cfg["restarts"],
        "maxiter": q_cfg["maxiter"],
        "shots": q_cfg["shots"],
        "sa_sweeps": c["sa_sweeps"],
        "sa_reads": c["sa_reads"],
    }

    jobs = [
        (
            0,
            "headline",
            tuple(raw["data"]["tickers"]),
            raw["problem"]["k"],
            float(raw["problem"]["q"]),
            settings,
            cfg.seed,
            raw,
        )
    ]
    specs = robustness_specs(
        raw["data"]["universe"], b["universe_size"], b["q_values"], b["instances"], cfg.seed
    )
    for i, (tickers, q) in enumerate(specs, start=1):
        jobs.append((i, "robustness", tickers, b["k"], q, settings, cfg.seed + i, raw))

    print(f"{len(jobs)} instances, {args.workers} workers, fast={is_fast_mode()}", flush=True)
    t0 = time.perf_counter()
    # NOTE(achintya): instances run in parallel processes so the full run fits in minutes.
    # Each method's wall time is still measured inside its own process, but CPU contention
    # can inflate it slightly; we record the worker count so readers know.
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        instances = sorted(pool.map(_run, jobs), key=lambda r: r["id"])
    total = time.perf_counter() - t0

    robust = [r for r in instances if r["kind"] == "robustness"]
    out = save_result(
        {
            "settings": {
                **settings,
                "fast_mode": is_fast_mode(),
                "workers": args.workers,
                "total_seconds": total,
            },
            "instances": instances,
            "headline": instances[0]["methods"],
            "summary": summarise(robust),
            "gaps": {"headline": instances[0]["gap"], "robustness": gap_stats(robust)},
        },
        args.out,
    )
    print(f"wrote {Path(out)} in {total:.0f} s")


if __name__ == "__main__":
    main()
