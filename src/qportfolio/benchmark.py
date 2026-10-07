"""Fair multi-instance benchmark: classical baselines vs penalty-QAOA vs XY-QAOA.

Rules are in docs/05_BENCHMARK_PROTOCOL.md. Every method is scored by the same function
(``metrics.evaluate_counts``) against the same brute-force reference: deterministic methods
contribute one "shot" (their answer), samplers contribute all their shots / reads.
I/O lives in ``scripts/run_benchmark.py``; everything here is pure.
"""

from __future__ import annotations

import time
from collections import Counter
from math import comb
from typing import Any

import numpy as np

from qportfolio.circuits import build_qaoa
from qportfolio.classical import brute_force, greedy, simulated_annealing
from qportfolio.hardware import cost_gap
from qportfolio.metrics import approximation_ratio, evaluate_counts
from qportfolio.problem import PortfolioProblem, x_to_bitstring
from qportfolio.qaoa import optimize, sample

# Method order is also the plotting order in viz.py.
PENALTY_REPS = (1, 2)
XY_REPS = (1, 2, 3)
METHODS = (
    ["random", "brute_force", "greedy", "simulated_annealing"]
    + [f"penalty_qaoa_p{r}" for r in PENALTY_REPS]
    + [f"xy_qaoa_p{r}" for r in XY_REPS]
)
METRICS = ("p_feasible", "p_optimal", "p_top2", "approx_ratio", "seconds", "evaluations")


def robustness_specs(
    universe: list[str], size: int, q_values: list[float], instances: int, seed: int
) -> list[tuple[tuple[str, ...], float]]:
    """Distinct random ``size``-subsets of ``universe`` crossed with every q, first ``instances``.

    Each subset is paired with all q values (subset-major order), so 24 instances = 8 subsets ×
    3 risk levels. Subsets keep the universe order so the tickers read the same way everywhere.
    """
    rng = np.random.default_rng(seed)
    n_subsets = -(-instances // len(q_values))  # ceiling division
    subsets: list[tuple[str, ...]] = []
    while len(subsets) < n_subsets:
        idx = np.sort(rng.choice(len(universe), size=size, replace=False))
        s = tuple(universe[i] for i in idx)
        if s not in subsets:
            subsets.append(s)
    specs = [(s, float(q)) for s in subsets for q in q_values]
    return specs[:instances]


def random_baseline(costs: np.ndarray) -> dict[str, Any]:
    """Analytic metrics of a uniformly random feasible basket (the floor)."""
    n = len(costs)
    return {
        "p_feasible": 1.0,
        "p_optimal": 1 / n,
        "p_top2": min(2, n) / n,
        # E[C] of a uniform guess is the mean feasible cost.
        "approx_ratio": approximation_ratio(costs.mean(), costs.min(), costs.max()),
        "top1_is_optimal": None,  # a random guess has no "most frequent" answer
        "seconds": 0.0,
        "evaluations": 0,
    }


def _score(counts: dict[str, int], p, costs, best_x, seconds: float, evaluations: int) -> dict:
    m = evaluate_counts(counts, p, costs, best_x)
    return {**m, "seconds": seconds, "evaluations": evaluations}


def basket_table(p: PortfolioProblem, costs: np.ndarray) -> list[dict[str, Any]]:
    """Every feasible basket with its equal-weight annual return and risk (for the frontier)."""
    rows = []
    for x, c in zip(p.feasible_set(), costs, strict=True):
        w = x / p.k  # equal weight (ADR 0003)
        rows.append(
            {
                "bits": x_to_bitstring(x),
                "assets": [lab for lab, b in zip(p.labels or (), x, strict=False) if b],
                "return": float(p.mu @ w),
                "risk": float(np.sqrt(w @ p.sigma @ w)),
                "cost": float(c),
            }
        )
    return rows


def run_instance(
    p: PortfolioProblem, settings: dict[str, Any], seed: int, keep_counts: bool = False
) -> dict[str, Any]:
    """Run every method in ``METHODS`` on one instance and score them identically.

    ``settings`` keys: restarts, maxiter, shots, sa_sweeps, sa_reads. ``keep_counts`` stores
    the raw QAOA / SA counts (only for the headline instance, to keep the JSON small).
    Wall time includes QAOA angle optimisation on the statevector, not just sampling (§5).
    """
    best, costs = brute_force(p)
    lam = p.default_penalty()  # the SAME λ for penalty-QAOA and SA (§1)
    methods: dict[str, dict[str, Any]] = {"random": random_baseline(costs)}
    counts_out: dict[str, dict[str, int]] = {}

    methods["brute_force"] = _score(
        {x_to_bitstring(best.x): 1}, p, costs, best.x, best.seconds, best.evaluations
    )
    g = greedy(p)
    methods["greedy"] = _score({x_to_bitstring(g.x): 1}, p, costs, best.x, g.seconds, g.evaluations)

    sa = simulated_annealing(p, lam, settings["sa_sweeps"], seed, reads=settings["sa_reads"])
    sa_counts = dict(Counter(x_to_bitstring(x) for x in sa.samples))
    methods["simulated_annealing"] = _score(sa_counts, p, costs, best.x, sa.seconds, sa.evaluations)
    counts_out["simulated_annealing"] = sa_counts

    for variant, reps_list in (("penalty", PENALTY_REPS), ("xy", XY_REPS)):
        for reps in reps_list:
            name = f"{variant}_qaoa_p{reps}"
            ansatz, H = build_qaoa(p, reps=reps, variant=variant, penalty=lam)
            res = optimize(ansatz, H, settings["restarts"], settings["maxiter"], seed)
            t0 = time.perf_counter()
            counts = sample(ansatz, res.params, shots=settings["shots"], seed=seed)
            seconds = res.seconds + time.perf_counter() - t0
            methods[name] = _score(counts, p, costs, best.x, seconds, res.nfev)
            methods[name]["energy"] = res.energy
            counts_out[name] = counts

    out = {
        "n": p.n,
        "k": p.k,
        "q": p.q,
        "n_feasible": comb(p.n, p.k),
        "penalty": lam,
        "optimum": {"x": best.x, "bits": x_to_bitstring(best.x), "cost": best.cost},
        "gap": cost_gap(p),
        "feasible_costs": costs,
        "methods": methods,
    }
    if keep_counts:
        out["counts"] = counts_out
        out["baskets"] = basket_table(p, costs)
    return out


def summarise(instances: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Mean ± std of every metric per method, plus the share of instances where top-1 is optimal.

    Std is the population std (ddof = 0) across instances, not a confidence interval.
    """
    summary: dict[str, dict[str, Any]] = {}
    for name in METHODS:
        rows = [inst["methods"][name] for inst in instances]
        s: dict[str, Any] = {"instances": len(rows)}
        for key in METRICS:
            vals = np.array([r[key] for r in rows], dtype=float)
            s[f"{key}_mean"] = float(vals.mean())
            s[f"{key}_std"] = float(vals.std())
        top1 = [r["top1_is_optimal"] for r in rows if r["top1_is_optimal"] is not None]
        s["top1_is_optimal_share"] = float(np.mean(top1)) if top1 else None
        summary[name] = s
    return summary


def gap_stats(instances: list[dict[str, Any]]) -> dict[str, float]:
    """Optimum-vs-runner-up gap as a share of the feasible cost range (how near-tied they are)."""
    rel = np.array([inst["gap"]["gap"] / inst["gap"]["cost_range"] for inst in instances])
    return {
        "relative_gap_mean": float(rel.mean()),
        "relative_gap_median": float(np.median(rel)),
        "relative_gap_min": float(rel.min()),
    }
