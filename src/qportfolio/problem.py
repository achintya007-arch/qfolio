"""The cardinality-constrained mean–variance problem and its QUBO / Ising forms.

Minimise C(x) = q xᵀΣx − μᵀx subject to Σx = k, x ∈ {0,1}ⁿ (docs/03_METHODOLOGY.md §1–3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
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
        raise NotImplementedError

    def cost(self, x: np.ndarray) -> float:
        """Objective C(x) = q xᵀΣx − μᵀx (lower is better)."""
        raise NotImplementedError

    def feasible_set(self) -> np.ndarray:
        """All weight-k bit vectors, shape (C(n, k), n)."""
        raise NotImplementedError

    def to_qubo(self, penalty: float = 0.0) -> tuple[np.ndarray, float]:
        """Return (Q, const) with xᵀQx + const = C(x) + penalty·(Σx − k)²."""
        raise NotImplementedError

    def to_ising(self, penalty: float = 0.0, normalize: bool = True) -> SparsePauliOp:
        """Cost Hamiltonian as Z / ZZ Pauli terms (constant dropped, optionally max-normalised)."""
        raise NotImplementedError

    def default_penalty(self) -> float:
        """λ = feasible-cost range (max − min), shared by penalty-QAOA and SA for fairness."""
        raise NotImplementedError


def bitstring_to_x(bits: str) -> np.ndarray:
    """Convert a Qiskit bitstring to x. Qiskit is little-endian: rightmost char = asset 0.

    This is the ONLY place bit order is handled (CLAUDE.md rule).
    """
    raise NotImplementedError


def x_to_bitstring(x: np.ndarray) -> str:
    """Inverse of :func:`bitstring_to_x`."""
    raise NotImplementedError
