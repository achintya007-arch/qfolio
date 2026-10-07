"""Score sampled bitstrings against the brute-force optimum (docs/03_METHODOLOGY.md §5)."""

from __future__ import annotations

import numpy as np

from qportfolio.problem import PortfolioProblem


def evaluate_counts(
    counts: dict[str, int],
    p: PortfolioProblem,
    feasible_costs: np.ndarray,
    best_x: np.ndarray,
) -> dict[str, float]:
    """Return p_feasible, p_optimal, p_optimal_postselected, approx_ratio,
    top1_is_optimal, expected_cost and shots for a counts dict.
    """
    raise NotImplementedError


def approximation_ratio(expected_cost: float, c_min: float, c_max: float) -> float:
    """(C_max − E[C | feasible]) / (C_max − C_min): 1 = always optimal, 0 = always worst."""
    raise NotImplementedError
