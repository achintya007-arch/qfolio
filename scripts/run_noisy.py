"""Noise study on fake IBM backends → ``results/noisy.json`` (docs/03 §6, P4).

Hardware instance (4 assets, k = 2), XY-QAOA p = 1, 2 with statevector-trained angles (the
same training as ``run_hardware.py``, so the angles match the real job). Per backend:
transpile report for levels 0-3, then raw → post-selected → post-selected + readout-mitigated.

    .venv\\Scripts\\python scripts/run_noisy.py
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from qiskit.quantum_info import Statevector

from qportfolio import noise
from qportfolio.circuits import build_qaoa
from qportfolio.config import is_fast_mode, load_config
from qportfolio.data import load_prices, returns_stats
from qportfolio.hardware import cost_gap
from qportfolio.io import save_result
from qportfolio.metrics import evaluate_counts
from qportfolio.problem import PortfolioProblem
from qportfolio.qaoa import optimize


def hardware_problem(raw: dict[str, Any]) -> PortfolioProblem:
    """The 4-asset, k = 2 instance from ``hardware_problem`` in the config."""
    d, hp = raw["data"], raw["hardware_problem"]
    mu, sigma = returns_stats(load_prices(d["path"], hp["tickers"], d["start"], d["end"]))
    labels = tuple(t.removesuffix(".NS") for t in hp["tickers"])
    return PortfolioProblem(mu, sigma, k=hp["k"], q=hp["q"], labels=labels)


def main() -> None:
    """Run the noise study and write ``results/noisy.json``."""
    cfg = load_config()
    raw, q, ncfg = cfg.raw, cfg.raw["qaoa"], cfg.raw["noise"]
    shots = q["shots"]
    p = hardware_problem(raw)
    feas = p.feasible_set()
    costs = np.array([p.cost(x) for x in feas])
    best_x = feas[costs.argmin()]

    def score(counts: dict[str, Any]) -> dict[str, Any]:
        return evaluate_counts(counts, p, costs, best_x)

    circuits, params, ideal = {}, {}, {}
    for reps in ncfg["reps"]:
        ansatz, H = build_qaoa(p, reps=reps, variant="xy")
        res = optimize(ansatz, H, restarts=q["restarts"], maxiter=q["maxiter"], seed=cfg.seed)
        circ = ansatz.assign_parameters(res.params)
        circuits[reps] = circ
        params[str(reps)] = res.params
        ideal[str(reps)] = score(Statevector(circ).probabilities_dict())
        print(f"p={reps}: ideal P(optimal) = {ideal[str(reps)]['p_optimal']:.3f}")

    backends = {}
    for name in ncfg["backends"]:
        backend = noise.fake_backend(name)
        t0 = time.perf_counter()
        transpile = {}
        runs = []
        for reps, circ in circuits.items():
            report = noise.transpile_report(circ, backend, tuple(ncfg["opt_levels"]), cfg.seed)
            transpile[str(reps)] = report.to_dict(orient="records")
            counts, layout = noise.run_noisy(circ, backend, shots, cfg.seed)
            mats = noise.readout_calibration(backend, layout, shots, cfg.seed)
            post = noise.postselect(counts, p.k)
            mitigated = noise.readout_mitigate(counts, mats)
            runs.append(
                {
                    "reps": reps,
                    "layout": layout,
                    "counts": counts,
                    "readout_matrices": mats,
                    "raw": score(counts),
                    "postselected": score(post),
                    "mitigated": score(mitigated),
                    "post_mitigated": score(noise.postselect(mitigated, p.k)),
                }
            )
            r = runs[-1]
            print(
                f"{backend.name} p={reps}: P(opt) raw {r['raw']['p_optimal']:.3f} -> "
                f"post-sel {r['postselected']['p_optimal']:.3f} -> "
                f"post-sel + mitigated {r['post_mitigated']['p_optimal']:.3f}"
            )
        backends[backend.name] = {
            "transpile": transpile,
            "runs": runs,
            "seconds": time.perf_counter() - t0,
        }

    out = save_result(
        {
            "instance": {"tickers": list(p.labels), "k": p.k, "q": p.q, **cost_gap(p)},
            "shots": shots,
            "fast_mode": is_fast_mode(),
            "params": params,  # QAOAAnsatz order: all β, then all γ
            "ideal": ideal,
            "backends": backends,
            "p_random": 1 / len(feas),
        },
        "results/noisy.json",
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
