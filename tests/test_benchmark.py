"""Benchmark plumbing: instance generation, the random floor, one tiny end-to-end instance."""

from math import comb

import numpy as np
import pytest

from qportfolio.benchmark import (
    METHODS,
    gap_stats,
    random_baseline,
    robustness_specs,
    run_instance,
    summarise,
)
from qportfolio.data import synthetic_instance
from qportfolio.problem import PortfolioProblem

UNIVERSE = [f"T{i}" for i in range(10)]
TINY = {"restarts": 1, "maxiter": 15, "shots": 256, "sa_sweeps": 50, "sa_reads": 10}


def test_robustness_specs_deterministic_and_distinct():
    a = robustness_specs(UNIVERSE, 6, [0.25, 0.5, 1.0], 24, seed=1)
    assert a == robustness_specs(UNIVERSE, 6, [0.25, 0.5, 1.0], 24, seed=1)
    assert len(a) == 24
    subsets = {s for s, _ in a}
    assert len(subsets) == 8  # 8 distinct subsets × 3 q values
    assert all(len(s) == 6 and set(s) <= set(UNIVERSE) for s in subsets)


def test_robustness_specs_truncates_for_fast_mode():
    assert len(robustness_specs(UNIVERSE, 6, [0.25, 0.5, 1.0], 4, seed=1)) == 4


def test_random_baseline_is_analytic():
    costs = np.array([0.0, 1.0, 2.0, 3.0])
    r = random_baseline(costs)
    assert r["p_optimal"] == 0.25 and r["p_top2"] == 0.5
    assert r["approx_ratio"] == pytest.approx(0.5)  # mean cost sits mid-range here


@pytest.fixture(scope="module")
def tiny_instance():
    mu, sigma = synthetic_instance(4, seed=5)
    p = PortfolioProblem(mu, sigma, k=2, q=0.5, labels=("A", "B", "C", "D"))
    return run_instance(p, TINY, seed=0, keep_counts=True)


def test_run_instance_scores_every_method(tiny_instance):
    m = tiny_instance["methods"]
    assert list(m) == METHODS
    assert m["brute_force"]["p_optimal"] == m["brute_force"]["approx_ratio"] == 1.0
    assert m["random"]["p_optimal"] == pytest.approx(1 / comb(4, 2))
    for name in METHODS:
        assert 0.0 <= m[name]["p_optimal"] <= m[name]["p_top2"] <= m[name]["p_feasible"] <= 1.0
    for reps in (1, 2, 3):  # the XY mixer never leaves the feasible subspace (AC4)
        assert m[f"xy_qaoa_p{reps}"]["p_feasible"] == pytest.approx(1.0)
    assert len(tiny_instance["baskets"]) == comb(4, 2)
    assert tiny_instance["gap"]["gap"] >= 0


def test_summarise_mean_std(tiny_instance):
    s = summarise([tiny_instance, tiny_instance])
    assert s["brute_force"]["p_optimal_mean"] == 1.0
    assert s["brute_force"]["p_optimal_std"] == 0.0
    assert s["brute_force"]["top1_is_optimal_share"] == 1.0
    assert s["random"]["top1_is_optimal_share"] is None
    assert 0 <= gap_stats([tiny_instance])["relative_gap_min"] <= 1
