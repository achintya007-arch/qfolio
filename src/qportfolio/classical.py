"""Classical baselines on the identical objective: brute force, simulated annealing, greedy.

Fairness rules are in docs/05_BENCHMARK_PROTOCOL.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from qportfolio.problem import PortfolioProblem


@dataclass
class ClassicalResult:
    """Best portfolio found by a classical method, plus its cost budget."""

    x: np.ndarray
    cost: float
    evaluations: int
    seconds: float
    method: str


def brute_force(p: PortfolioProblem) -> tuple[ClassicalResult, np.ndarray]:
    """Enumerate all C(n, k) feasible baskets; return (best, every feasible cost)."""
    raise NotImplementedError


def simulated_annealing(
    p: PortfolioProblem, penalty: float, sweeps: int, seed: int
) -> ClassicalResult:
    """Single-flip SA on the penalty QUBO with a geometric temperature schedule."""
    raise NotImplementedError


def greedy(p: PortfolioProblem) -> ClassicalResult:
    """Add the asset with the best marginal cost until k are chosen ("the Excel analyst")."""
    raise NotImplementedError
