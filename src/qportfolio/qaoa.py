"""Optimise QAOA angles on the exact statevector energy, then sample with any V2 sampler."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from scipy.optimize import minimize

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
    """Warm-start angles in ``QAOAAnsatz`` order: all β first, then all γ (pitfall #6).

    A discretised annealing schedule: β ramps down and γ ramps up across the layers.
    """
    frac = (np.arange(reps) + 0.5) / reps
    return np.concatenate([(1 - frac) * delta, frac * delta])


def optimize(
    ansatz: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    restarts: int,
    maxiter: int,
    seed: int,
) -> QAOAResult:
    """Minimise ⟨H⟩ with ``StatevectorEstimator`` + COBYLA over several restarts.

    Restart 0 uses the linear-ramp warm start; the others start from uniform random angles
    in [−π/2, π/2]. We optimise the exact expectation value, not a sampled estimate
    (pitfall #7): it is noise-free, so COBYLA converges faster and reproducibly.
    """
    rng = np.random.default_rng(seed)
    estimator = StatevectorEstimator()
    num_params = ansatz.num_parameters

    def energy(theta: np.ndarray, trace: list[float]) -> float:
        value = float(estimator.run([(ansatz, hamiltonian, theta)]).result()[0].data.evs)
        trace.append(value)
        return value

    starts = [linear_ramp_init(num_params // 2)] + [
        rng.uniform(-np.pi / 2, np.pi / 2, num_params) for _ in range(restarts - 1)
    ]
    t0 = time.perf_counter()
    best, best_trace, nfev = None, [], 0
    for x0 in starts:
        trace: list[float] = []
        res = minimize(energy, x0, args=(trace,), method="COBYLA", options={"maxiter": maxiter})
        nfev += res.nfev
        if best is None or res.fun < best.fun:
            best, best_trace = res, trace
    return QAOAResult(
        params=np.asarray(best.x),
        energy=float(best.fun),
        history=best_trace,
        nfev=nfev,
        seconds=time.perf_counter() - t0,
    )


def sample(
    ansatz: QuantumCircuit,
    params: np.ndarray,
    sampler: Any = None,
    shots: int = 4096,
    seed: int | None = None,
) -> dict[str, int]:
    """Bind ``params``, measure all qubits and return counts (statevector sampler by default).

    ``seed`` only seeds the default ``StatevectorSampler``; pass your own ``sampler``
    (Aer / IBM Runtime ``SamplerV2``) for noisy or hardware runs.
    """
    sampler = sampler or StatevectorSampler(seed=seed)
    circ = ansatz.assign_parameters(params)
    circ.measure_all()
    return sampler.run([circ], shots=shots).result()[0].data.meas.get_counts()
