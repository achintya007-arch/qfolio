"""Smoke tests: the package and every module import, and the toolchain is Qiskit 2.x."""

import importlib

import pytest

import qportfolio

MODULES = [
    "config",
    "data",
    "problem",
    "classical",
    "circuits",
    "qaoa",
    "metrics",
    "noise",
    "hardware",
    "viz",
    "io",
    "demo",
]


def test_package_imports():
    assert qportfolio.__version__
    assert callable(qportfolio.bitstring_to_x)


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(f"qportfolio.{name}")


def test_demo_runs(capsys):
    from qportfolio.demo import main

    main()
    assert "checkpoint" in capsys.readouterr().out


# NOTE(achintya): CI runs `pytest -m slow`, which exits with code 5 ("no tests collected")
# until the real slow QAOA tests exist. This environment check keeps that step meaningful.
@pytest.mark.slow
def test_qiskit_v2_primitives_available():
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorSampler

    assert int(qiskit.__version__.split(".")[0]) >= 2

    bell = QuantumCircuit(2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()
    counts = StatevectorSampler(seed=0).run([bell], shots=256).result()[0].data.meas.get_counts()
    assert set(counts) <= {"00", "11"}
