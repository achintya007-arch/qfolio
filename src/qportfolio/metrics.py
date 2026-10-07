"""Score sampled bitstrings against the brute-force optimum (docs/03_METHODOLOGY.md §5)."""

from __future__ import annotations

import numpy as np

from qportfolio.problem import PortfolioProblem, bitstring_to_x


def evaluate_counts(
    counts: dict[str, int],
    p: PortfolioProblem,
    feasible_costs: np.ndarray,
    best_x: np.ndarray,
) -> dict[str, float]:
    """Return p_feasible, p_optimal, p_optimal_postselected, approx_ratio,
    top1_is_optimal, expected_cost and shots for a counts dict.

    ``feasible_costs`` and ``best_x`` come from ``classical.brute_force`` so every method is
    scored against the same reference. Infeasible samples count towards ``shots`` but not
    towards ``expected_cost`` / ``approx_ratio`` (those are conditional on feasibility).
    """
    best_x = np.asarray(best_x)
    shots = sum(counts.values())
    n_feasible = n_optimal = 0
    cost_sum = 0.0
    top_count, top_x = -1, None
    for bits, c in counts.items():
        x = bitstring_to_x(bits)
        if x.sum() != p.k:
            continue
        n_feasible += c
        cost_sum += c * p.cost(x)
        if c > top_count:  # most frequent *feasible* bitstring
            top_count, top_x = c, x
        if (x == best_x).all():
            n_optimal += c

    expected_cost = cost_sum / n_feasible if n_feasible else float("nan")
    return {
        "p_feasible": n_feasible / shots,
        "p_optimal": n_optimal / shots,
        "p_optimal_postselected": n_optimal / n_feasible if n_feasible else 0.0,
        "approx_ratio": (
            approximation_ratio(expected_cost, feasible_costs.min(), feasible_costs.max())
            if n_feasible
            else 0.0
        ),
        "top1_is_optimal": bool(top_x is not None and (top_x == best_x).all()),
        "expected_cost": expected_cost,
        "shots": shots,
    }


def approximation_ratio(expected_cost: float, c_min: float, c_max: float) -> float:
    """(C_max − E[C | feasible]) / (C_max − C_min): 1 = always optimal, 0 = always worst."""
    return float((c_max - expected_cost) / (c_max - c_min))
