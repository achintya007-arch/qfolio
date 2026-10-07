"""Noise-aware layer: fake backends, transpiler study, post-selection, readout mitigation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd
    from qiskit import QuantumCircuit


def fake_backend(name: str = "FakeTorino") -> Any:
    """Instantiate a ``qiskit_ibm_runtime.fake_provider`` backend by class name."""
    raise NotImplementedError


def transpile_report(
    circ: QuantumCircuit, backend: Any, levels: tuple[int, ...] = (0, 1, 2, 3), seed: int = 0
) -> pd.DataFrame:
    """Depth, 2-qubit gate count and estimated fidelity per optimisation level."""
    raise NotImplementedError


def run_noisy(circ: QuantumCircuit, backend: Any, shots: int, seed: int) -> dict[str, int]:
    """Transpile and run on ``AerSimulator.from_backend(backend)``; return counts."""
    raise NotImplementedError


def postselect(counts: dict[str, int], k: int) -> dict[str, int]:
    """Keep only weight-k bitstrings (valid as error detection only for the XY circuit)."""
    raise NotImplementedError


def readout_calibration(backend: Any, layout: list[int], shots: int, seed: int) -> list[np.ndarray]:
    """Per-qubit 2×2 confusion matrices M[measured, prepared] from all-0 / all-1 circuits."""
    raise NotImplementedError


def readout_mitigate(counts: dict[str, int], cal_mats: list[np.ndarray]) -> dict[str, float]:
    """Tensored-inverse readout correction; negatives clipped and renormalised."""
    raise NotImplementedError
