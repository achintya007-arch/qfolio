"""Every figure renders from small inputs and is written as PNG + SVG."""

import pytest

from qportfolio import viz
from qportfolio.benchmark import run_instance, scaling_rows, summarise
from qportfolio.data import synthetic_instance
from qportfolio.io import load_result
from qportfolio.problem import PortfolioProblem

TINY = {"restarts": 1, "maxiter": 10, "shots": 128, "sa_sweeps": 30, "sa_reads": 5}


@pytest.fixture(scope="module")
def bench():
    mu, sigma = synthetic_instance(4, seed=7)
    p = PortfolioProblem(mu, sigma, k=2, q=0.5, labels=("A", "B", "C", "D"))
    inst = run_instance(p, TINY, seed=0, keep_counts=True)
    inst.update(id=0, kind="headline", tickers=["A.NS", "B.NS", "C.NS", "D.NS"])
    return {"instances": [inst], "summary": summarise([inst])}


@pytest.mark.parametrize("name", ["headline", "feasibility", "distribution", "frontier"])
def test_benchmark_figures(bench, name, tmp_path):
    png = viz.save_figure(getattr(viz, name)(bench), name, tmp_path)
    assert png.exists() and png.with_suffix(".svg").exists()


def test_noise_ladder_from_committed_hardware(tmp_path):
    hw = load_result("results/hardware/db3b1bimb58s7387e0jg.json")
    dry = load_result("results/hardware/dry_run_fake_torino.json")
    ideal = {str(r["reps"]): {"p_optimal": 0.6} for r in hw["runs"]}
    png = viz.save_figure(viz.noise_ladder(ideal, dry, hw), "noise_ladder", tmp_path)
    assert png.exists()


def test_scaling(tmp_path):
    rows = scaling_rows(ns=(4, 6))
    assert rows[0]["feasible"] == 6 and rows[1]["all_bitstrings"] == 64
    assert viz.save_figure(viz.scaling(rows), "scaling", tmp_path).exists()
