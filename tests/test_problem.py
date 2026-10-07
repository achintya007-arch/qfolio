"""PortfolioProblem: QUBO / Ising mappings (AC1, AC2) and bit order."""

from itertools import product
from math import comb

import numpy as np
import pytest

from qportfolio.data import synthetic_instance
from qportfolio.problem import PortfolioProblem, bitstring_to_x, x_to_bitstring


@pytest.fixture
def problem() -> PortfolioProblem:
    mu, sigma = synthetic_instance(6, seed=7)
    return PortfolioProblem(mu, sigma, k=3, q=0.5)


def qubo_energies(Q: np.ndarray) -> np.ndarray:
    """xᵀQx for every basis state, indexed like a statevector (integer of the bitstring)."""
    n = len(Q)
    xs = [bitstring_to_x(format(i, f"0{n}b")) for i in range(2**n)]
    return np.array([x @ Q @ x for x in xs])


@pytest.mark.parametrize("lam", [0.0, 0.37, 2.0])
def test_qubo_matches_objective_all_bitstrings(problem, lam):
    """AC1: xᵀQx + const == C(x) + λ(Σx − k)² for every one of the 2ⁿ bitstrings."""
    Q, const = problem.to_qubo(lam)
    for x in map(np.array, product([0, 1], repeat=problem.n)):
        expected = problem.cost(x) + lam * (x.sum() - problem.k) ** 2
        assert x @ Q @ x + const == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("lam", [0.0, 1.5])
@pytest.mark.parametrize("normalize", [True, False])
def test_ising_diagonal_matches_qubo(problem, lam, normalize):
    """AC2: H's diagonal is an affine map (positive scale, constant shift) of the QUBO energies."""
    Q, _ = problem.to_qubo(lam)
    diag = np.real(np.diag(problem.to_ising(lam, normalize=normalize).to_matrix()))
    scaled = qubo_energies(Q) / (np.abs(Q).max() if normalize else 1.0)
    shift = scaled - diag  # the dropped constant: must be the same for every bitstring
    np.testing.assert_allclose(shift, shift[0], atol=1e-12)
    assert diag.argmin() == scaled.argmin()  # same best portfolio


def test_bitstring_roundtrip_little_endian():
    # Rightmost char = qubit 0 = asset 0.
    np.testing.assert_array_equal(bitstring_to_x("001"), [1, 0, 0])
    np.testing.assert_array_equal(bitstring_to_x("110"), [0, 1, 1])
    assert x_to_bitstring(np.array([1, 0, 0, 1, 1])) == "11001"
    for bits in ("000000", "101100", "011011", "111111"):
        assert x_to_bitstring(bitstring_to_x(bits)) == bits


@pytest.mark.parametrize(("n", "k"), [(4, 2), (5, 2), (6, 3), (6, 1)])
def test_feasible_set_size(n, k):
    mu, sigma = synthetic_instance(n, seed=1)
    feas = PortfolioProblem(mu, sigma, k=k).feasible_set()
    assert feas.shape == (comb(n, k), n)
    assert (feas.sum(axis=1) == k).all()
    assert len({tuple(r) for r in feas}) == comb(n, k)


def test_cost_definition(problem):
    x = np.array([1, 0, 1, 0, 1, 0])
    expected = problem.q * x @ problem.sigma @ x - problem.mu @ x
    assert problem.cost(x) == pytest.approx(expected)


def test_default_penalty_is_feasible_cost_range(problem):
    costs = [problem.cost(x) for x in problem.feasible_set()]
    assert problem.default_penalty() == pytest.approx(max(costs) - min(costs))
    assert problem.default_penalty() > 0
