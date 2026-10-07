"""Results JSON carries reproducibility metadata and round-trips NumPy values."""

import numpy as np

from qportfolio.io import load_result, save_result


def test_save_load_roundtrip(tmp_path):
    path = save_result({"x": np.array([1, 0, 1]), "cost": np.float64(-0.1)}, tmp_path / "r.json")
    data = load_result(path)
    assert data["x"] == [1, 0, 1]
    assert data["cost"] == -0.1
    assert set(data["meta"]) == {"created", "git_sha", "config_hash", "versions"}
    assert "qiskit" in data["meta"]["versions"]
