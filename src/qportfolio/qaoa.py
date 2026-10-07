"""Optimise QAOA angles on the exact statevector energy, then sample with any V2 sampler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp


@dataclass
class QAOAResult:
    """Best angles found over all restarts, with the energy trace of the winning run."""

    params: np.ndarray
    energy: float
    history: list[float]
    nfev: int
    seconds: float


def linear_ramp_init(reps: int, delta: float = 0.75) -> np.ndarray:
    """Warm-start angles in ``QAOAAnsatz`` order: all β first, then all γ (pitfall #6)."""
    raise NotImplementedError


def optimize(
    ansatz: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    restarts: int,
    maxiter: int,
    seed: int,
) -> QAOAResult:
    """Minimise ⟨H⟩ with ``StatevectorEstimator`` + COBYLA over several restarts."""
    raise NotImplementedError


def sample(
    ansatz: QuantumCircuit,
    params: np.ndarray,
    sampler: Any = None,
    shots: int = 4096,
) -> dict[str, int]:
    """Bind ``params``, measure all qubits and return counts (statevector sampler by default)."""
    raise NotImplementedError
