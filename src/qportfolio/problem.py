"""The cardinality-constrained mean–variance problem and its QUBO / Ising forms.

Minimise C(x) = q xᵀΣx − μᵀx subject to Σx = k, x ∈ {0,1}ⁿ (docs/03_METHODOLOGY.md §1–3).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
from qiskit.quantum_info import SparsePauliOp


@dataclass(frozen=True)
class PortfolioProblem:
    """Pick exactly ``k`` of ``n`` assets (equal weight) to minimise q·risk − return.

    Attributes
    ----------
    mu : np.ndarray
        Annualised mean returns, shape (n,).
    sigma : np.ndarray
        Annualised covariance, shape (n, n).
    k : int
        Number of assets to hold.
    q : float
        Risk aversion (0.25 growth, 0.5 balanced, 1.0 conservative).
    labels : tuple[str, ...] | None
        Optional ticker names, in qubit order.
    """

    mu: np.ndarray
    sigma: np.ndarray
    k: int
    q: float = 0.5
    labels: tuple[str, ...] | None = None

    @property
    def n(self) -> int:
        """Number of candidate assets (= number of qubits)."""
        return len(self.mu)

    def cost(self, x: np.ndarray) -> float:
        """Objective C(x) = q xᵀΣx − μᵀx (lower is better)."""
        x = np.asarray(x, dtype=float)
        return float(self.q * x @ self.sigma @ x - self.mu @ x)

    def feasible_set(self) -> np.ndarray:
        """All weight-k bit vectors, shape (C(n, k), n)."""
        rows = []
        for idx in combinations(range(self.n), self.k):
            x = np.zeros(self.n, dtype=int)
            x[list(idx)] = 1
            rows.append(x)
        return np.array(rows)

    def to_qubo(self, penalty: float = 0.0) -> tuple[np.ndarray, float]:
        """Return (Q, const) with xᵀQx + const = C(x) + penalty·(Σx − k)².

        Expanding λ(Σx − k)² with x_i² = x_i gives λ on every off-diagonal pair,
        λ(1 − 2k) on the diagonal and the constant λk² (docs/03 §2).
        """
        n, k, lam = self.n, self.k, penalty
        Q = self.q * self.sigma - np.diag(self.mu)
        Q = Q + lam * (np.ones((n, n)) - np.eye(n)) + lam * (1 - 2 * k) * np.eye(n)
        return Q, lam * k**2

    def to_ising(self, penalty: float = 0.0, normalize: bool = True) -> SparsePauliOp:
        """Cost Hamiltonian as Z / ZZ Pauli terms (constant dropped, optionally max-normalised).

        Substitutes x_i = (1 − z_i)/2. The constant offset is dropped because it only shifts
        energies, and dividing by max|Q| keeps QAOA angles of order 1 (docs/03 §3).
        """
        Q, _ = self.to_qubo(penalty)
        if normalize:
            Q = Q / np.abs(Q).max()
        n = self.n
        terms, h = [], np.zeros(n)
        for i in range(n):
            h[i] -= Q[i, i] / 2
            for j in range(i + 1, n):
                w = (Q[i, j] + Q[j, i]) / 4
                h[i] -= w
                h[j] -= w
                terms.append(("ZZ", [i, j], w))
        terms += [("Z", [i], h[i]) for i in range(n)]
        return SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()

    def default_penalty(self) -> float:
        """λ = feasible-cost range (max − min), shared by penalty-QAOA and SA for fairness."""
        c = [self.cost(x) for x in self.feasible_set()]
        return float(max(c) - min(c))


def bitstring_to_x(bits: str) -> np.ndarray:
    """Convert a Qiskit bitstring to x. Qiskit is little-endian: rightmost char = asset 0.

    This is the ONLY place bit order is handled (CLAUDE.md rule).
    """
    return np.array([int(b) for b in reversed(bits)], dtype=int)


def x_to_bitstring(x: np.ndarray) -> str:
    """Inverse of :func:`bitstring_to_x`."""
    return "".join(str(int(b)) for b in reversed(np.asarray(x)))
