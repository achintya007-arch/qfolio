"""Submit to / collect from IBM Quantum via ``qiskit_ibm_runtime.SamplerV2``.

The token is read by ``QiskitRuntimeService()`` from ``~/.qiskit/qiskit-ibm.json`` or the
``QISKIT_IBM_TOKEN`` env var. Never print or log it. Not used in CI.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    from qiskit import QuantumCircuit


def submit(
    circ: QuantumCircuit,
    params: np.ndarray,
    backend_name: str | None,
    shots: int,
    options: dict[str, Any],
) -> str:
    """Transpile for the backend, submit one SamplerV2 job and return its job id."""
    raise NotImplementedError


def collect(job_id: str) -> dict[str, Any]:
    """Fetch a finished job: counts per PUB, backend name, timestamps, calibration snapshot."""
    raise NotImplementedError


def save_evidence(record: dict[str, Any], outdir: str | Path = "results/hardware") -> Path:
    """Write ``<job_id>.json`` so judges can verify the hardware run."""
    raise NotImplementedError
