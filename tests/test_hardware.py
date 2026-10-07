"""Hardware path: readout helpers (fast) and an end-to-end ``--dry-run`` on FakeTorino (slow).

No test touches the network: the dry run must never construct ``QiskitRuntimeService``.
"""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from qportfolio import hardware as hw
from qportfolio.problem import PortfolioProblem

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_hardware.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("run_hardware", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readout_matrices_from_calibration_counts():
    # Qubit 0 (rightmost char) flips 0→1 10% of the time; qubit 1 is perfect.
    counts0 = {"00": 90, "01": 10}
    counts1 = {"11": 80, "10": 20}  # qubit 0 reads 0 when prepared 1 in 20% of shots
    m0, m1 = hw.readout_matrices(counts0, counts1, n=2)
    np.testing.assert_allclose(m0, [[0.9, 0.2], [0.1, 0.8]])  # M[measured, prepared]
    np.testing.assert_allclose(m1, np.eye(2))


def test_readout_mitigate_inverts_known_error():
    m = np.array([[0.9, 0.2], [0.1, 0.8]])
    # True state |01⟩ (qubit 0 = 1); qubit 0's readout error smears it into |00⟩.
    noisy = {"01": 800, "00": 200}
    fixed = hw.readout_mitigate(noisy, [m, np.eye(2)])
    assert fixed == pytest.approx({"01": 1.0})


def test_calibration_circuits_prepare_all_zero_and_all_one():
    zeros, ones = hw.calibration_circuits(3)
    assert zeros.count_ops().get("x", 0) == 0
    assert ones.count_ops()["x"] == 3
    assert zeros.num_clbits == ones.num_clbits == 3


def test_cost_gap_orders_best_two():
    p = PortfolioProblem(mu=np.array([0.3, 0.2, 0.1]), sigma=np.zeros((3, 3)), k=1)
    gap = hw.cost_gap(p)
    assert gap["best_bits"] == "001" and gap["second_bits"] == "010"  # little-endian
    assert gap["gap"] == pytest.approx(0.1)


@pytest.mark.slow
def test_dry_run_on_fake_torino(tmp_path, monkeypatch, capsys):
    import qiskit_ibm_runtime

    def no_network(*args, **kwargs):
        raise AssertionError("dry run must not contact IBM Quantum")

    monkeypatch.setattr(qiskit_ibm_runtime, "QiskitRuntimeService", no_network)
    monkeypatch.setenv("QFOLIO_FAST", "1")
    _load_script().main(["--dry-run", "--outdir", str(tmp_path)])

    assert "cost gap best→second" in capsys.readouterr().out
    record = json.loads((tmp_path / "dry_run_fake_torino.json").read_text(encoding="utf-8"))
    assert record["dry_run"] and record["backend"] == "fake_torino"
    assert [r["reps"] for r in record["runs"]] == [1, 2]
    for run in record["runs"]:
        assert sum(run["counts"].values()) == record["shots"]
        assert run["postselected"]["p_feasible"] == 1.0
        # Noisy, but the trained angles still beat a uniform random basket (1/6).
        assert run["raw"]["p_optimal"] > record["p_random"]
    assert len(record["readout_matrices"]) == len(record["calibrated_qubits"])


def test_real_backend_options_have_no_simulator_fields():
    # IBM rejects a job with any simulator.* option (error 3211), so real runs must omit them.
    from qiskit_ibm_runtime.options import SamplerOptions

    opts = hw.sampler_options(8192, seed=2026, dd=True, twirl=True, simulator=False)
    assert "simulator" not in opts
    parsed = SamplerOptions(**opts)  # the options must still be valid SamplerV2 options
    assert parsed.default_shots == 8192
    assert parsed.dynamical_decoupling.sequence_type == "XY4"
    assert all(not str(k).startswith("simulator") for k in _flatten(opts))


def test_fake_backend_options_keep_simulator_seed():
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit_ibm_runtime.fake_provider import FakeTorino

    assert hw.is_fake_backend(FakeTorino())
    assert not hw.is_fake_backend(GenericBackendV2(4))  # stands in for a real device
    opts = hw.sampler_options(1024, seed=7, dd=False, twirl=False, simulator=True)
    assert opts["simulator"] == {"seed_simulator": 7}


def _flatten(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}{k}"
        yield key
        if isinstance(v, dict):
            yield from _flatten(v, f"{key}.")
