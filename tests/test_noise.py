"""Noise layer: readout mitigation, post-selection, transpile report (docs/08)."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from qportfolio.noise import (
    estimated_fidelity,
    fake_backend,
    postselect,
    readout_mitigate,
    transpile_report,
)


def test_readout_mitigation_recovers_ideal():
    # Ideal distribution on 2 qubits, then independent flips: qubit i reads wrong with e0/e1.
    ideal = {"00": 0.5, "01": 0.2, "10": 0.0, "11": 0.3}
    mats = [np.array([[0.97, 0.06], [0.03, 0.94]]), np.array([[0.95, 0.08], [0.05, 0.92]])]
    noisy = {}
    for b_true, p in ideal.items():
        for b_meas in ideal:
            # little-endian: rightmost char is qubit 0
            prob = p
            for i in range(2):
                prob *= mats[i][int(b_meas[1 - i]), int(b_true[1 - i])]
            noisy[b_meas] = noisy.get(b_meas, 0.0) + prob
    shots = 10**6
    counts = {b: round(v * shots) for b, v in noisy.items()}
    fixed = readout_mitigate(counts, mats)
    for b, p in ideal.items():
        assert fixed.get(b, 0.0) == pytest.approx(p, abs=1e-3)


def test_postselect_drops_wrong_weight():
    counts = {"0011": 5, "0111": 3, "1010": 2, "0000": 1}
    assert postselect(counts, 2) == {"0011": 5, "1010": 2}


def test_transpile_report_columns():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    backend = fake_backend("FakeTorino")
    df = transpile_report(qc, backend, levels=(0, 3), seed=0)
    assert list(df["level"]) == [0, 3]
    assert {"depth", "two_qubit_gates", "est_fidelity", "layout"} <= set(df.columns)
    assert (df["two_qubit_gates"] >= 1).all()
    assert ((df["est_fidelity"] > 0) & (df["est_fidelity"] <= 1)).all()


def test_estimated_fidelity_of_empty_circuit_is_one():
    assert estimated_fidelity(QuantumCircuit(1), fake_backend("FakeTorino")) == 1.0
