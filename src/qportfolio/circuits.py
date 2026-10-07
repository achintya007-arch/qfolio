"""QAOA circuits: Dicke initial state, weight-conserving XY-ring mixer, full ansatz.

See docs/04_IMPLEMENTATION_NOTES.md (pitfalls #1, #5, #6) before changing anything here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp

    from qportfolio.problem import PortfolioProblem


def dicke_state(n: int, k: int) -> QuantumCircuit:
    """Uniform superposition over all n-bit strings of weight k (Bärtschi–Eidenbenz 2019)."""
    raise NotImplementedError


def xy_ring_mixer(n: int) -> QuantumCircuit:
    """Parity-ordered ring of ``XXPlusYYGate(2β)``; one Parameter β; conserves Hamming weight."""
    raise NotImplementedError


def build_qaoa(
    p: PortfolioProblem,
    reps: int,
    variant: Literal["penalty", "xy"],
    penalty: float | None = None,
) -> tuple[QuantumCircuit, SparsePauliOp]:
    """Return (parameterised ansatz, cost Hamiltonian) for the penalty or XY variant."""
    raise NotImplementedError
