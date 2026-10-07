"""Classical baselines are correct and operate on the same objective."""

from itertools import product

import numpy as np
import pytest

from qportfolio.classical import brute_force, greedy, simulated_annealing
from qportfolio.data import synthetic_instance
from qportfolio.problem import PortfolioProblem


@pytest.fixture(params=[(6, 3, 7), (5, 2, 11), (4, 2, 3)])
def problem(request) -> PortfolioProblem:
    n, k, seed = request.param
    mu, sigma = synthetic_instance(n, seed=seed)
    return PortfolioProblem(mu, sigma, k=k, q=0.5)


def test_brute_force_matches_exhaustive(problem):
    best, costs = brute_force(problem)
    # Independent check: scan all 2ⁿ strings and keep the weight-k ones.
    feasible = [np.array(x) for x in product([0, 1], repeat=problem.n) if sum(x) == problem.k]
    exhaustive = min(feasible, key=problem.cost)
    np.testing.assert_array_equal(best.x, exhaustive)
    assert best.cost == pytest.approx(problem.cost(exhaustive))
    assert len(costs) == len(feasible) == best.evaluations
    assert costs.min() == pytest.approx(best.cost)


def test_sa_finds_optimum_small(problem):
    best, _ = brute_force(problem)
    res = simulated_annealing(problem, problem.default_penalty(), sweeps=500, seed=0, reads=40)
    # The best read is the optimum ...
    np.testing.assert_array_equal(res.x, best.x)
    assert res.cost == pytest.approx(best.cost)
    assert res.samples.shape == (40, problem.n)
    # ... and individual reads beat a uniformly random feasible guess (1 / C(n, k)).
    p_opt = np.mean([(s == best.x).all() for s in res.samples])
    assert p_opt > 1 / len(problem.feasible_set())


def test_sa_is_reproducible(problem):
    lam = problem.default_penalty()
    a = simulated_annealing(problem, lam, sweeps=50, seed=42, reads=5)
    b = simulated_annealing(problem, lam, sweeps=50, seed=42, reads=5)
    np.testing.assert_array_equal(a.samples, b.samples)


def test_greedy_returns_feasible(problem):
    res = greedy(problem)
    assert res.x.sum() == problem.k
    assert res.cost == pytest.approx(problem.cost(res.x))
    best, _ = brute_force(problem)
    assert res.cost >= best.cost - 1e-12
