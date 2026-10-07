"""QAOA circuits: Dicke initial state, weight-conserving XY-ring mixer, full ansatz.

See docs/04_IMPLEMENTATION_NOTES.md (pitfalls #1, #5, #6) before changing anything here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import QAOAAnsatz, RYGate, XXPlusYYGate

if TYPE_CHECKING:
    from qiskit.quantum_info import SparsePauliOp

    from qportfolio.problem import PortfolioProblem


def _scs(qc: QuantumCircuit, m: int, k: int) -> None:
    """Append the split-and-cyclic-shift block SCS_{m,k} acting on qubits 0..m-1.

    Each block moves amplitude so that, after all blocks, every weight-k string has
    equal amplitude 1/sqrt(C(n, k)). The rotation angles come from Bärtschi & Eidenbenz
    (2019), "Deterministic preparation of Dicke states".
    """
    a, b = m - 2, m - 1
    qc.cx(a, b)
    qc.cry(2 * np.arccos(np.sqrt(1 / m)), b, a)
    qc.cx(a, b)
    for l in range(2, k + 1):  # noqa: E741 (l matches the paper's notation)
        a, mid = m - 1 - l, m - l
        qc.cx(a, b)
        qc.append(RYGate(2 * np.arccos(np.sqrt(l / m))).control(2), [b, mid, a])
        qc.cx(a, b)


def dicke_state(n: int, k: int) -> QuantumCircuit:
    """Uniform superposition over all n-bit strings of weight k (Bärtschi–Eidenbenz 2019).

    NOTE(achintya): a generic ``StatePreparation`` gives the same state but is deeper on
    hardware (depth 324 vs 233 at n=6, pitfall #5), so we build the structured circuit.
    """
    qc = QuantumCircuit(n, name=f"Dicke({n},{k})")
    for i in range(n - k, n):  # start from |1..10..0⟩ (k ones on the top qubits)
        qc.x(i)
    for m in range(n, k, -1):
        _scs(qc, m, k)
    for m in range(k, 1, -1):
        _scs(qc, m, m - 1)
    return qc


def xy_ring_mixer(n: int) -> QuantumCircuit:
    """Parity-ordered ring of ``XXPlusYYGate(2β)``; one Parameter β; conserves Hamming weight.

    Each ``XXPlusYYGate`` only swaps amplitude between |01⟩ and |10⟩, so the number of
    selected assets never changes. Edges are applied even-first, then odd, so gates in one
    layer touch disjoint qubits.

    Do NOT pass the mixer as a ``SparsePauliOp``: ``QAOAAnsatz`` would Trotterise the XX and
    YY terms separately, which breaks weight conservation (P(feasible) = 0.94, pitfall #1).
    """
    beta = Parameter("β")
    qc = QuantumCircuit(n, name="XY-ring")
    edges = [(i, (i + 1) % n) for i in range(n)] if n > 2 else [(0, 1)]
    for i, j in edges[0::2] + edges[1::2]:
        qc.append(XXPlusYYGate(2 * beta), [i, j])
    return qc


def build_qaoa(
    p: PortfolioProblem,
    reps: int,
    variant: Literal["penalty", "xy"],
    penalty: float | None = None,
) -> tuple[QuantumCircuit, SparsePauliOp]:
    """Return (parameterised ansatz, cost Hamiltonian) for the penalty or XY variant.

    - ``"xy"``: Dicke(n, k) start + XY-ring mixer. The constraint is enforced by the circuit,
      so H carries no penalty term.
    - ``"penalty"``: |+⟩ⁿ start + standard X mixer; the constraint is a penalty λ(Σx − k)²
      in H (λ defaults to ``p.default_penalty()``).

    Parameters are ordered all β first, then all γ (``QAOAAnsatz`` sorts by name, pitfall #6).
    """
    if variant == "xy":
        H = p.to_ising(0.0)
        ansatz = QAOAAnsatz(
            H, reps=reps, initial_state=dicke_state(p.n, p.k), mixer_operator=xy_ring_mixer(p.n)
        )
    elif variant == "penalty":
        H = p.to_ising(p.default_penalty() if penalty is None else penalty)
        ansatz = QAOAAnsatz(H, reps=reps)
    else:
        raise ValueError(f"unknown variant {variant!r}; use 'xy' or 'penalty'")
    # Decompose the QAOAAnsatz wrapper into plain gates so it can be drawn and transpiled.
    return ansatz.decompose(reps=3), H
