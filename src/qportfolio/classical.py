"""Classical baselines on the identical objective: brute force, simulated annealing, greedy.

Fairness rules are in docs/05_BENCHMARK_PROTOCOL.md.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from qportfolio.problem import PortfolioProblem


@dataclass
class ClassicalResult:
    """Best portfolio found by a classical method, plus its cost budget.

    ``samples`` holds every read's final x for samplers (SA), so P(optimal) can be computed
    the same way as for QAOA shots; it is ``None`` for deterministic methods.
    """

    x: np.ndarray
    cost: float
    evaluations: int
    seconds: float
    method: str
    samples: np.ndarray | None = None


def brute_force(p: PortfolioProblem) -> tuple[ClassicalResult, np.ndarray]:
    """Enumerate all C(n, k) feasible baskets; return (best, every feasible cost).

    The cost array is in the same order as ``p.feasible_set()``.
    """
    t0 = time.perf_counter()
    feas = p.feasible_set()
    costs = np.array([p.cost(x) for x in feas])
    i = int(costs.argmin())
    seconds = time.perf_counter() - t0
    best = ClassicalResult(feas[i], float(costs[i]), len(feas), seconds, "brute_force")
    return best, costs


def simulated_annealing(
    p: PortfolioProblem, penalty: float, sweeps: int, seed: int, reads: int = 1
) -> ClassicalResult:
    """Single-flip SA on the penalty QUBO with a geometric temperature schedule.

    Each read starts from a random bitstring and runs ``sweeps`` sweeps of n single-bit flip
    proposals. The returned ``x`` is the best *feasible* final state over all reads (scored on
    C(x), not on the QUBO energy, per docs/05 §1); ``samples`` holds every read's final state.
    """
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)
    Q, const = p.to_qubo(penalty)
    Qs = Q + Q.T  # symmetric form for the flip-energy formula below
    n = p.n

    # NOTE(achintya): swapping one asset for another takes two single flips and passes through
    # an infeasible state that costs ≈ λ. So the schedule starts at T = λ (barrier crossable)
    # and cools geometrically to λ/100 (frozen). Even so, single-flip SA freezes into *some*
    # feasible basket before it can tell close costs apart: per-read P(opt) is modest, the best
    # over many reads is reliable. Same weakness as penalty-QAOA, which is the point of XY.
    t_hot, t_cold = max(penalty, 1e-9), max(penalty, 1e-9) / 100
    temps = t_hot * (t_cold / t_hot) ** (np.arange(sweeps) / max(sweeps - 1, 1))

    finals, evaluations = [], 0
    for _ in range(reads):
        x = rng.integers(0, 2, n)
        for t in temps:
            for i in rng.permutation(n):
                # Energy change of flipping bit i in xᵀQx: (1 − 2x_i)(Q_ii + Σ_{j≠i} Qs_ij x_j)
                d = 1 - 2 * x[i]
                delta = d * (Q[i, i] + Qs[i] @ x - Qs[i, i] * x[i])
                evaluations += 1
                if delta <= 0 or rng.random() < np.exp(-delta / t):
                    x[i] ^= 1
        finals.append(x.copy())

    samples = np.array(finals)
    feasible = [x for x in samples if x.sum() == p.k]
    if feasible:
        best = min(feasible, key=p.cost)
        cost = p.cost(best)
    else:  # no read ended feasible: report the lowest-energy state, cost = penalised energy
        best = min(samples, key=lambda x: x @ Q @ x)
        cost = float(best @ Q @ best + const)
    seconds = time.perf_counter() - t0
    return ClassicalResult(best, float(cost), evaluations, seconds, "simulated_annealing", samples)


def greedy(p: PortfolioProblem) -> ClassicalResult:
    """Add the asset with the best marginal cost until k are chosen ("the Excel analyst")."""
    t0 = time.perf_counter()
    x = np.zeros(p.n, dtype=int)
    evaluations = 0
    for _ in range(p.k):
        best_i, best_c = -1, np.inf
        for i in np.flatnonzero(x == 0):
            x[i] = 1
            c = p.cost(x)
            evaluations += 1
            x[i] = 0
            if c < best_c:
                best_i, best_c = i, c
        x[best_i] = 1
    seconds = time.perf_counter() - t0
    return ClassicalResult(x, p.cost(x), evaluations, seconds, "greedy")
