"""Metric definitions on hand-built counts (n = 4, k = 2)."""

import numpy as np
import pytest

from qportfolio.classical import brute_force
from qportfolio.data import synthetic_instance
from qportfolio.metrics import approximation_ratio, evaluate_counts
from qportfolio.problem import PortfolioProblem, x_to_bitstring


@pytest.fixture
def setup():
    mu, sigma = synthetic_instance(4, seed=3)
    p = PortfolioProblem(mu, sigma, k=2)
    best, costs = brute_force(p)
    worst = p.feasible_set()[costs.argmax()]
    return p, best, costs, x_to_bitstring(best.x), x_to_bitstring(worst)


def test_known_counts(setup):
    p, best, costs, opt, worst = setup
    # 60 optimal, 20 worst-feasible, 20 infeasible (weight 3).
    counts = {opt: 60, worst: 20, "0111": 20}
    m = evaluate_counts(counts, p, costs, best.x)
    assert m["shots"] == 100
    assert m["p_feasible"] == pytest.approx(0.8)
    assert m["p_optimal"] == pytest.approx(0.6)
    assert m["p_optimal_postselected"] == pytest.approx(0.75)
    assert m["top1_is_optimal"] is True
    # E[C | feasible] = 0.75 C_min + 0.25 C_max  →  AR = 0.75
    assert m["expected_cost"] == pytest.approx(0.75 * costs.min() + 0.25 * costs.max())
    assert m["approx_ratio"] == pytest.approx(0.75)


def test_all_infeasible(setup):
    p, best, costs, *_ = setup
    m = evaluate_counts({"1111": 10, "0000": 5}, p, costs, best.x)
    assert m["p_feasible"] == m["p_optimal"] == m["approx_ratio"] == 0.0
    assert m["top1_is_optimal"] is False
    assert np.isnan(m["expected_cost"])


def test_approximation_ratio_endpoints():
    assert approximation_ratio(-1.0, -1.0, 2.0) == 1.0
    assert approximation_ratio(2.0, -1.0, 2.0) == 0.0
