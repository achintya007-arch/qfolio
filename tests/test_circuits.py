"""Circuits do what the method claims: Dicke start, weight-conserving mixer, β-before-γ order."""

from math import comb

import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from qportfolio.circuits import build_qaoa, dicke_state, xy_ring_mixer
from qportfolio.data import synthetic_instance
from qportfolio.problem import PortfolioProblem


def _weight_k_probs(sv: Statevector, k: int) -> np.ndarray:
    """Probability mass on weight-k basis states (index popcount = Hamming weight)."""
    probs = sv.probabilities()
    return np.array([pr for i, pr in enumerate(probs) if i.bit_count() == k])


@pytest.mark.parametrize(("n", "k"), [(4, 2), (5, 2), (6, 3)])
def test_dicke_uniform_weight_k(n, k):
    # AC3: amplitude 1/C(n,k) on every weight-k string, nothing anywhere else.
    sv = Statevector(dicke_state(n, k))
    weight_k = _weight_k_probs(sv, k)
    assert len(weight_k) == comb(n, k)
    np.testing.assert_allclose(weight_k, 1 / comb(n, k), atol=1e-9)
    assert abs(1 - weight_k.sum()) < 1e-9


@pytest.mark.parametrize("n", [4, 6])
def test_xy_mixer_conserves_weight(n):
    # AC4: start in Dicke(n, 2), apply the mixer at random β, stay in the weight-2 subspace.
    rng = np.random.default_rng(0)
    mixer = xy_ring_mixer(n)
    assert mixer.num_parameters == 1
    for beta in rng.uniform(-np.pi, np.pi, 5):
        sv = Statevector(dicke_state(n, 2).compose(mixer.assign_parameters([beta])))
        assert _weight_k_probs(sv, 2).sum() == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("reps", [1, 2])
def test_xy_qaoa_ideal_p_feasible_is_one(reps):
    # AC4 on the full ansatz: random (β, γ) never leaks out of the feasible subspace.
    mu, sigma = synthetic_instance(6, seed=7)
    p = PortfolioProblem(mu, sigma, k=3)
    ansatz, _ = build_qaoa(p, reps=reps, variant="xy")
    theta = np.random.default_rng(1).uniform(-np.pi, np.pi, ansatz.num_parameters)
    sv = Statevector(ansatz.assign_parameters(theta))
    assert _weight_k_probs(sv, 3).sum() == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("variant", ["xy", "penalty"])
def test_qaoa_parameter_order(variant):
    # Pitfall #6: QAOAAnsatz sorts parameters by name, so all β come before all γ.
    mu, sigma = synthetic_instance(4, seed=3)
    ansatz, _ = build_qaoa(PortfolioProblem(mu, sigma, k=2), reps=3, variant=variant)
    names = [prm.name for prm in ansatz.parameters]
    assert names == ["β[0]", "β[1]", "β[2]", "γ[0]", "γ[1]", "γ[2]"]


def test_build_qaoa_rejects_unknown_variant():
    mu, sigma = synthetic_instance(4, seed=3)
    with pytest.raises(ValueError, match="unknown variant"):
        build_qaoa(PortfolioProblem(mu, sigma, k=2), reps=1, variant="grover")
