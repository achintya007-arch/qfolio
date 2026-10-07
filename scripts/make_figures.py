"""Build every figure in docs/05 §7 from ``results/*.json`` → ``results/figures/`` (PNG + SVG).

    .venv\\Scripts\\python scripts/make_figures.py

Figures whose input JSON is missing are skipped with a message, so this also works on a
fresh clone before the noise study has been run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # files only, no GUI window (the notebook keeps its inline backend)
import numpy as np  # noqa: E402
from qiskit.quantum_info import Statevector

from qportfolio import viz
from qportfolio.benchmark import scaling_rows
from qportfolio.circuits import build_qaoa
from qportfolio.config import load_config
from qportfolio.data import load_prices, returns_stats
from qportfolio.hardware import cost_gap
from qportfolio.io import load_result
from qportfolio.metrics import evaluate_counts
from qportfolio.problem import PortfolioProblem

RESULTS = Path("results")
HARDWARE_JOB = RESULTS / "hardware" / "db3b1bimb58s7387e0jg.json"
DRY_RUN = RESULTS / "hardware" / "dry_run_fake_torino.json"


def ideal_from_hardware(hardware: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Exact (statevector) metrics of the very angles that were sent to the device.

    This is the top rung of the noise ladder: same circuit, same parameters, no noise.
    """
    inst = hardware["instance"]
    d = load_config().raw["data"]
    tickers = [f"{t}.NS" for t in inst["tickers"]]  # stored without the exchange suffix
    mu, sigma = returns_stats(load_prices(d["path"], tickers, d["start"], d["end"]))
    p = PortfolioProblem(mu, sigma, k=inst["k"], q=inst["q"])
    assert np.isclose(cost_gap(p)["best_cost"], inst["best_cost"]), "instance mismatch"
    feas = p.feasible_set()
    costs = np.array([p.cost(x) for x in feas])
    out = {}
    for reps, params in hardware["params"].items():
        ansatz, _ = build_qaoa(p, reps=int(reps), variant="xy")
        probs = Statevector(ansatz.assign_parameters(params)).probabilities_dict()
        out[reps] = evaluate_counts(probs, p, costs, feas[costs.argmin()])
    return out


def main() -> None:
    """Write all figures whose inputs exist."""
    made = []
    bench_path = RESULTS / "benchmark.json"
    hardware = load_result(HARDWARE_JOB) if HARDWARE_JOB.exists() else None
    if bench_path.exists():
        bench = load_result(bench_path)
        made.append(viz.save_figure(viz.headline(bench), "headline"))
        made.append(viz.save_figure(viz.feasibility(bench), "feasibility"))
        made.append(viz.save_figure(viz.distribution(bench), "distribution"))
        made.append(viz.save_figure(viz.frontier(bench), "frontier"))
    else:
        print(f"skip figures 1, 2, 3, 6: {bench_path} not found (run scripts/run_benchmark.py)")

    if hardware is not None and DRY_RUN.exists():
        ladder = viz.noise_ladder(ideal_from_hardware(hardware), load_result(DRY_RUN), hardware)
        made.append(viz.save_figure(ladder, "noise_ladder"))
    else:
        print("skip figure 4: hardware / dry-run JSON not found")

    noisy_path = RESULTS / "noisy.json"
    if noisy_path.exists():
        made.append(viz.save_figure(viz.transpile(load_result(noisy_path)), "transpile"))
    else:
        print(f"skip figure 5: {noisy_path} not found (run scripts/run_noisy.py)")

    made.append(viz.save_figure(viz.scaling(scaling_rows(), hardware), "scaling"))
    for path in made:
        print(f"wrote {path} (+ .svg)")


if __name__ == "__main__":
    main()
