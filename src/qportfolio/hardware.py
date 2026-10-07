"""Run fixed-angle XY-QAOA on IBM Quantum via ``qiskit_ibm_runtime.SamplerV2``.

One job holds every circuit (docs/06_HARDWARE_RUNBOOK.md §1), so we queue only once:
PUB 0..R-1 are the QAOA circuits (one per depth p), the last two PUBs are readout calibration
(all-0 and all-X) on the same physical qubits. ``--dry-run`` sends the identical PUBs through
the identical ``SamplerV2`` code path, but to ``FakeTorino`` (local Aer simulation).

The token is read by ``QiskitRuntimeService()`` from ``~/.qiskit/qiskit-ibm.json`` or the
``QISKIT_IBM_TOKEN`` env var. This module never reads, prints or logs it. Not used in CI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager

from qportfolio.metrics import evaluate_counts
from qportfolio.problem import PortfolioProblem, bitstring_to_x, x_to_bitstring

if TYPE_CHECKING:
    from qiskit.providers import BackendV2

_TWO_QUBIT_GATES = ("cz", "ecr", "cx")


def get_backend(name: str | None, dry_run: bool, min_qubits: int = 8) -> BackendV2:
    """Return ``FakeTorino`` for a dry run, else the named (or least busy) IBM device.

    Only the non-dry-run branch touches the network.
    """
    if dry_run:
        from qiskit_ibm_runtime.fake_provider import FakeTorino

        return FakeTorino()
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()  # reads the saved account; we never see the token
    if name:
        return service.backend(name)
    return service.least_busy(operational=True, simulator=False, min_num_qubits=min_qubits)


def fetch_job(job_id: str) -> Any:
    """Look up a submitted job by id (works from a different process or day)."""
    from qiskit_ibm_runtime import QiskitRuntimeService

    return QiskitRuntimeService().job(job_id)


def cost_gap(p: PortfolioProblem) -> dict[str, Any]:
    """Best and second-best feasible baskets and their cost gap (how hard the instance is).

    A small gap means noise can easily swap the top two, so P(top-2) matters as well as
    P(optimal) (docs/03_METHODOLOGY.md §5).
    """
    feas = p.feasible_set()
    costs = np.array([p.cost(x) for x in feas])
    first, second = np.argsort(costs)[:2]
    return {
        "best_bits": x_to_bitstring(feas[first]),
        "second_bits": x_to_bitstring(feas[second]),
        "best_cost": float(costs[first]),
        "second_cost": float(costs[second]),
        "gap": float(costs[second] - costs[first]),
        "cost_range": float(costs.max() - costs.min()),
    }


def calibration_circuits(n: int) -> list[QuantumCircuit]:
    """Two n-qubit readout-calibration circuits: prepare all-0, and all-1 (X on every qubit)."""
    zeros = QuantumCircuit(n, name="cal_0")
    ones = QuantumCircuit(n, name="cal_1")
    ones.x(range(n))
    for qc in (zeros, ones):
        qc.measure_all()
    return [zeros, ones]


def readout_matrices(counts0: dict[str, int], counts1: dict[str, int], n: int) -> list[np.ndarray]:
    """Per-qubit 2×2 confusion matrices ``M[measured, prepared]`` from the two cal circuits.

    Column 0 comes from the all-0 run and column 1 from the all-1 run, using the marginal of
    each qubit. Assumes independent (uncorrelated) readout errors: the tensored model.
    NOTE(achintya): lives here, not in noise.py, because P4 (noise.py) is not built yet.
    """
    mats = []
    for i in range(n):
        cols = []
        for counts in (counts0, counts1):
            shots = sum(counts.values())
            p1 = sum(c for b, c in counts.items() if bitstring_to_x(b)[i] == 1) / shots
            cols.append([1 - p1, p1])
        mats.append(np.array(cols).T)  # rows = measured, columns = prepared
    return mats


def readout_mitigate(counts: dict[str, int], cal_mats: list[np.ndarray]) -> dict[str, float]:
    """Tensored-inverse readout correction (docs/04); negatives clipped and renormalised."""
    n = len(cal_mats)
    shots = sum(counts.values())
    vec = np.zeros(2**n)
    for b, c in counts.items():
        vec[int(b, 2)] = c / shots
    t = vec.reshape([2] * n)  # axis 0 = leftmost char = qubit n-1 (little-endian)
    for i, M in enumerate(cal_mats):
        axis = n - 1 - i
        t = np.moveaxis(np.tensordot(np.linalg.inv(M), t, axes=([1], [axis])), 0, axis)
    v = np.clip(t.reshape(-1), 0, None)
    v /= v.sum()
    return {format(i, f"0{n}b"): float(x) for i, x in enumerate(v) if x > 1e-12}


def transpile_pubs(
    qaoa_circuits: list[QuantumCircuit], backend: BackendV2, seed: int
) -> tuple[list[QuantumCircuit], list[list[int]], list[int]]:
    """Transpile QAOA circuits (opt level 3) and calibration circuits on the same qubits.

    Returns (ISA circuits, final layout per QAOA circuit, calibrated physical qubits).
    Routing may leave p=1 and p=2 measured on different physical qubits, so we calibrate the
    union of all measured qubits and later pick each circuit's matrices by physical index.
    """
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=seed)
    isa = [pm.run(c) for c in qaoa_circuits]
    layouts = [tc.layout.final_index_layout() for tc in isa]  # physical qubit per asset
    physical = sorted({q for lay in layouts for q in lay})
    cal_pm = generate_preset_pass_manager(
        optimization_level=1, backend=backend, initial_layout=physical, seed_transpiler=seed
    )
    isa += [cal_pm.run(c) for c in calibration_circuits(len(physical))]
    return isa, layouts, physical


def is_fake_backend(backend: BackendV2) -> bool:
    """True for ``qiskit_ibm_runtime.fake_provider`` backends (local Aer simulation)."""
    from qiskit_ibm_runtime.fake_provider.fake_backend import FakeBackendV2

    return isinstance(backend, FakeBackendV2)


def sampler_options(
    shots: int, seed: int, dd: bool, twirl: bool, simulator: bool
) -> dict[str, Any]:
    """``SamplerV2`` options: XY4 dynamical decoupling and gate + readout twirling.

    ``simulator`` adds ``simulator.seed_simulator``. It must be False for real devices:
    IBM rejects the whole job if any simulator field is set (error 3211, hit on 2026-10-08).
    """
    opts: dict[str, Any] = {
        "default_shots": shots,
        "dynamical_decoupling": {"enable": dd, **({"sequence_type": "XY4"} if dd else {})},
        "twirling": {"enable_gates": twirl, "enable_measure": twirl},
    }
    if simulator:
        opts["simulator"] = {"seed_simulator": seed}
    return opts


def configure_sampler(backend: BackendV2, shots: int, seed: int, dd: bool, twirl: bool) -> Any:
    """``SamplerV2`` in job mode with the options above; simulator seed only for fake backends.

    Open Plan supports job mode (sessions need a paid plan). On a fake backend the runtime
    runs locally on Aer and ignores DD / twirling, but the code path is the same.
    NOTE(achintya): we check the backend's type, not the --dry-run flag, so a real device can
    never receive simulator options, whatever flags the script was called with.
    """
    from qiskit_ibm_runtime import SamplerV2

    opts = sampler_options(shots, seed, dd, twirl, simulator=is_fake_backend(backend))
    return SamplerV2(mode=backend, options=opts)


def circuit_stats(tc: QuantumCircuit) -> dict[str, int]:
    """Depth and two-qubit gate count of a transpiled circuit."""
    ops = tc.count_ops()
    return {"depth": tc.depth(), "two_qubit_gates": sum(ops.get(g, 0) for g in _TWO_QUBIT_GATES)}


def backend_snapshot(backend: BackendV2, qubits: list[int]) -> dict[str, Any]:
    """Median T1/T2 (µs), readout error and 2q-gate error on the used physical qubits."""
    target = backend.target

    def median(values: list[float | None]) -> float | None:
        vals = [v for v in values if v is not None]
        return float(np.median(vals)) if vals else None

    props = [target.qubit_properties[q] if target.qubit_properties else None for q in qubits]
    meas = target.get("measure", {})
    two_q = next((g for g in _TWO_QUBIT_GATES if g in target), None)
    used = set(qubits)
    pair_errors = [
        ip.error
        for qargs, ip in (target[two_q].items() if two_q else [])
        if ip and set(qargs) <= used
    ]
    return {
        "qubits": qubits,
        "t1_us": median([pr.t1 * 1e6 if pr and pr.t1 else None for pr in props]),
        "t2_us": median([pr.t2 * 1e6 if pr and pr.t2 else None for pr in props]),
        "readout_error": median([meas[(q,)].error if (q,) in meas else None for q in qubits]),
        "two_qubit_gate": two_q,
        "two_qubit_error": median(pair_errors),
    }


def summarise(
    p: PortfolioProblem, pub_counts: list[dict[str, int]], meta: dict[str, Any]
) -> dict[str, Any]:
    """Raw / post-selected / readout-mitigated metrics for every QAOA PUB of one job.

    ``pub_counts`` is in PUB order (QAOA circuits, then cal_0, cal_1). ``meta`` is the
    ``pending.json`` record written at submit time (reps, layouts, calibrated qubits, …).
    """
    feas = p.feasible_set()
    costs = np.array([p.cost(x) for x in feas])
    best_x = feas[costs.argmin()]
    physical = meta["calibrated_qubits"]
    all_mats = readout_matrices(pub_counts[-2], pub_counts[-1], len(physical))

    def score(counts: dict[str, float]) -> dict[str, Any]:
        return evaluate_counts(counts, p, costs, best_x)  # includes p_top2

    runs = []
    for i, reps in enumerate(meta["reps"]):
        raw = pub_counts[i]
        # Each asset's matrix is the one measured on that asset's physical qubit.
        mats = [all_mats[physical.index(q)] for q in meta["layouts"][i]]
        post = {b: c for b, c in raw.items() if bitstring_to_x(b).sum() == p.k}
        mitigated = readout_mitigate(raw, mats)
        runs.append(
            {
                "reps": reps,
                "counts": raw,
                "raw": score(raw),
                "postselected": score(post) if post else None,
                "mitigated": score(mitigated),
            }
        )
    return {
        "calibration": {"counts_all0": pub_counts[-2], "counts_all1": pub_counts[-1]},
        "readout_matrices": {str(q): m for q, m in zip(physical, all_mats, strict=True)},
        "runs": runs,
        "p_random": 1 / len(feas),
    }
