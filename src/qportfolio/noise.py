"""Noise-aware layer: fake backends, transpiler study, post-selection, readout mitigation.

Runs locally on ``AerSimulator.from_backend`` (a noise model built from a real device's
calibration snapshot). The readout helpers are shared with ``hardware.py`` so the noisy
study and the real IBM job are mitigated by exactly the same code (docs/03 §6).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from qiskit.transpiler import generate_preset_pass_manager

from qportfolio.hardware import calibration_circuits, circuit_stats, readout_matrices
from qportfolio.hardware import readout_mitigate as readout_mitigate  # re-export, same code
from qportfolio.problem import bitstring_to_x

if TYPE_CHECKING:
    from qiskit import QuantumCircuit


def fake_backend(name: str = "FakeTorino") -> Any:
    """Instantiate a ``qiskit_ibm_runtime.fake_provider`` backend by class name."""
    from qiskit_ibm_runtime import fake_provider

    return getattr(fake_provider, name)()


def estimated_fidelity(tc: QuantumCircuit, backend: Any) -> float:
    """Product of (1 − error) over every gate and measurement, from the backend's error rates.

    A crude success estimate (it ignores idle decoherence and crosstalk) that is good for
    comparing transpiler settings on the same device, not for predicting absolute results.
    """
    target = backend.target
    fid = 1.0
    for inst in tc.data:
        name = inst.operation.name
        if name not in target:
            continue  # barrier, delay, …
        qargs = tuple(tc.find_bit(q).index for q in inst.qubits)
        props = target[name].get(qargs)
        if props is not None and props.error is not None:
            fid *= 1.0 - props.error
    return float(fid)


def _with_measurements(circ: QuantumCircuit) -> QuantumCircuit:
    if circ.num_clbits:
        return circ
    measured = circ.copy()
    measured.measure_all()
    return measured


def transpile_report(
    circ: QuantumCircuit, backend: Any, levels: tuple[int, ...] = (0, 1, 2, 3), seed: int = 0
) -> pd.DataFrame:
    """Depth, 2-qubit gate count and estimated fidelity per optimisation level."""
    circ = _with_measurements(circ)
    rows = []
    for level in levels:
        pm = generate_preset_pass_manager(
            optimization_level=level, backend=backend, seed_transpiler=seed
        )
        tc = pm.run(circ)
        rows.append(
            {
                "level": level,
                **circuit_stats(tc),
                "est_fidelity": estimated_fidelity(tc, backend),
                "layout": tc.layout.final_index_layout(),
            }
        )
    return pd.DataFrame(rows)


def run_noisy(
    circ: QuantumCircuit, backend: Any, shots: int, seed: int, level: int = 3
) -> tuple[dict[str, int], list[int]]:
    """Transpile (``level``, fixed seed) and run on ``AerSimulator.from_backend(backend)``.

    Returns (counts, physical qubit of each virtual qubit); the layout is needed to calibrate
    readout on the same physical qubits.
    """
    from qiskit_aer import AerSimulator

    pm = generate_preset_pass_manager(
        optimization_level=level, backend=backend, seed_transpiler=seed
    )
    tc = pm.run(_with_measurements(circ))
    sim = AerSimulator.from_backend(backend)
    counts = sim.run(tc, shots=shots, seed_simulator=seed).result().get_counts()
    return counts, tc.layout.final_index_layout()


def postselect(counts: dict[str, Any], k: int) -> dict[str, Any]:
    """Keep only weight-k bitstrings (valid as error detection only for the XY circuit)."""
    return {b: c for b, c in counts.items() if bitstring_to_x(b).sum() == k}


def readout_calibration(backend: Any, layout: list[int], shots: int, seed: int) -> list[np.ndarray]:
    """Per-qubit 2×2 confusion matrices M[measured, prepared] from all-0 / all-1 circuits.

    The calibration circuits are pinned to ``layout`` so each matrix belongs to the physical
    qubit that measured that asset in the QAOA run.
    """
    from qiskit_aer import AerSimulator

    pm = generate_preset_pass_manager(
        optimization_level=1, backend=backend, initial_layout=layout, seed_transpiler=seed
    )
    sim = AerSimulator.from_backend(backend)
    cal = [pm.run(c) for c in calibration_circuits(len(layout))]
    result = sim.run(cal, shots=shots, seed_simulator=seed).result()
    return readout_matrices(result.get_counts(0), result.get_counts(1), len(layout))
