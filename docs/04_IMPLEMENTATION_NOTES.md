# 04 · Implementation notes (verified on Qiskit 2.x)

Everything in this file was **executed and checked** before the build started
(qiskit 2.5, qiskit-aer 0.17, qiskit-ibm-runtime 0.50, Python 3.13). Claude Code should split this
reference into the modules listed in `02_ARCHITECTURE.md` instead of re-deriving it.

## Pitfalls we already hit (read these first)

| # | Pitfall | Symptom | Fix |
|---|---|---|---|
| 1 | **XY mixer passed as `SparsePauliOp` to `QAOAAnsatz`** | Ideal P(feasible) = 0.94 instead of 1.00. The default Trotter ordering applies all XX terms, then all YY terms, which breaks weight conservation | Build the mixer as a **circuit** of `XXPlusYYGate(2β)` on even edges, then odd edges (`xy_ring_mixer`). Also cut 2-qubit gates from 76 → 52 on FakeTorino |
| 2 | Penalty-QAOA "works" in the sense that it returns feasible strings | P(optimal) ≈ random (0.03–0.05 vs 0.05) for every λ ∈ {0.5, 1, 2}×range, also with CVaR α = 0.1 | This is a **result**, not a bug. Report it. It motivates the XY variant |
| 3 | Little-endian bitstrings | Wrong portfolio reported as optimal | Only ever use `bitstring_to_x()` |
| 4 | `Statevector.probabilities_dict()` returns ~1e-33 entries | Feasibility assertions fail | Filter `v > 1e-12` |
| 5 | Generic `StatePreparation` for the Dicke state | Deeper on hardware (324 vs 233 depth at n=6) | Use the Bärtschi–Eidenbenz circuit `dicke_state()` (exact, verified n≤6) |
| 6 | `QAOAAnsatz` parameter order | Warm start applied to the wrong angles | Parameters are sorted by name: all **β** first, then all **γ** |
| 7 | Optimising with sampled energies | Noisy, slow convergence | Optimise the exact ⟨H⟩ with `StatevectorEstimator`; sample only at the end |
| 8 | n = 6, k = 3 XY-QAOA on hardware | ~100+ two-qubit gates after routing, mostly noise | Hardware instance is **n = 4, k = 2** (52 two-qubit gates on Torino at p=1) |
| 9 | `yfinance` blocked behind proxies / in CI | Empty DataFrame | Fetch once locally, commit `data/prices.csv`; CI never touches the network |
| 10 | IBM channel name | `ibm_quantum` channel was retired with the classic platform | Use `channel="ibm_quantum_platform"` |
| 11 | `sampler.options.simulator.seed_simulator` set for a real device | Job `db3attimb58s7387dsd0` on ibm_kingston: `ERROR`, "Error code 3211; Job not valid. Options field seed_simulator is not valid for this backend". The FakeTorino dry run passed because local mode accepts it | Set `simulator.*` options only for `fake_provider` backends: `hardware.sampler_options(..., simulator=is_fake_backend(backend))`, checked by backend type, not by the CLI flag. Unit-tested |

## Validation numbers (synthetic instance, seed 7, n = 6, k = 3, 8192 shots): superseded

> **From a different pre-build generator, not reproducible here; superseded by `results/`.**

| Variant | p | P(feasible) | P(optimal) | Approx. ratio | Top-1 optimal | Random P(opt) |
|---|---|---|---|---|---|---|
| Penalty (X mixer) | 1 | 0.671 | 0.034 | 0.51 | no | 0.05 |
| Penalty (X mixer) | 2 | 0.793 | 0.047 | 0.53 | yes | 0.05 |
| **XY + Dicke** | 1 | **1.000** | **0.215** | 0.70 | **yes** | 0.05 |
| **XY + Dicke** | 2 | **1.000** | **0.318** | **0.84** | **yes** | 0.05 |

> NOTE (2026-10-08): the repo's `data.synthetic_instance(6, seed=7)` is not the generator used here:
> with it, XY p=1 gives P(opt) = 0.081 and its top-1 is not optimal. Quote only numbers from `results/`.

Noisy check (same pre-build generator, not reproducible here; superseded by `results/`)
(n = 4, k = 2, p = 1, random P(opt) = 0.167): ideal 0.656 → FakeTorino raw 0.499 → post-selected 0.603 (P(feasible) raw 0.83).

## Reference implementation

```python
from __future__ import annotations

import itertools
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import QAOAAnsatz, RYGate, XXPlusYYGate
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize


# ---------- problem.py ----------
def bitstring_to_x(bits: str) -> np.ndarray:
    """Qiskit bitstrings are little-endian: rightmost char = qubit 0 = asset 0."""
    return np.array([int(b) for b in reversed(bits)], dtype=int)


@dataclass(frozen=True)
class PortfolioProblem:
    mu: np.ndarray
    sigma: np.ndarray
    k: int
    q: float = 0.5

    @property
    def n(self) -> int:
        return len(self.mu)

    def cost(self, x) -> float:
        x = np.asarray(x, dtype=float)
        return float(self.q * x @ self.sigma @ x - self.mu @ x)

    def feasible_set(self) -> np.ndarray:
        rows = []
        for idx in combinations(range(self.n), self.k):
            x = np.zeros(self.n, dtype=int)
            x[list(idx)] = 1
            rows.append(x)
        return np.array(rows)

    def default_penalty(self) -> float:
        c = [self.cost(x) for x in self.feasible_set()]
        return float(max(c) - min(c))

    def to_qubo(self, penalty: float = 0.0) -> tuple[np.ndarray, float]:
        n, k, lam = self.n, self.k, penalty
        Q = self.q * self.sigma - np.diag(self.mu)
        Q = Q + lam * (np.ones((n, n)) - np.eye(n)) + lam * (1 - 2 * k) * np.eye(n)
        return Q, lam * k**2

    def to_ising(self, penalty: float = 0.0, normalize: bool = True) -> SparsePauliOp:
        Q, _ = self.to_qubo(penalty)
        if normalize:
            Q = Q / np.abs(Q).max()
        n = self.n
        terms, h = [], np.zeros(n)
        for i in range(n):
            h[i] -= Q[i, i] / 2
            for j in range(i + 1, n):
                w = (Q[i, j] + Q[j, i]) / 4
                h[i] -= w
                h[j] -= w
                terms.append(("ZZ", [i, j], w))
        terms += [("Z", [i], h[i]) for i in range(n)]
        return SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()


# ---------- circuits.py ----------
def _scs(qc: QuantumCircuit, m: int, k: int) -> None:
    """Split-and-cyclic-shift block SCS_{m,k} on qubits 0..m-1 (Bärtschi & Eidenbenz 2019)."""
    a, b = m - 2, m - 1
    qc.cx(a, b)
    qc.cry(2 * np.arccos(np.sqrt(1 / m)), b, a)
    qc.cx(a, b)
    for l in range(2, k + 1):
        a, mid = m - 1 - l, m - l
        qc.cx(a, b)
        qc.append(RYGate(2 * np.arccos(np.sqrt(l / m))).control(2), [b, mid, a])
        qc.cx(a, b)


def dicke_state(n: int, k: int) -> QuantumCircuit:
    """Uniform superposition over all n-bit strings with exactly k ones."""
    qc = QuantumCircuit(n, name=f"Dicke({n},{k})")
    for i in range(n - k, n):
        qc.x(i)
    for m in range(n, k, -1):
        _scs(qc, m, k)
    for m in range(k, 1, -1):
        _scs(qc, m, m - 1)
    return qc


def xy_ring_mixer(n: int) -> QuantumCircuit:
    """Parity-ordered ring XY mixer. Each XXPlusYYGate conserves Hamming weight exactly.

    Do NOT pass the mixer as a SparsePauliOp: QAOAAnsatz Trotterises the XX and YY terms
    in an order that breaks weight conservation (measured P(feasible)=0.94 instead of 1.0).
    """
    beta = Parameter("β")
    qc = QuantumCircuit(n, name="XY-ring")
    edges = [(i, (i + 1) % n) for i in range(n)] if n > 2 else [(0, 1)]
    for i, j in edges[0::2] + edges[1::2]:
        qc.append(XXPlusYYGate(2 * beta), [i, j])
    return qc


def build_qaoa(p: PortfolioProblem, reps: int, variant: str, penalty: float | None = None):
    if variant == "xy":
        H = p.to_ising(0.0)
        ans = QAOAAnsatz(H, reps=reps, initial_state=dicke_state(p.n, p.k),
                         mixer_operator=xy_ring_mixer(p.n))
    elif variant == "penalty":
        H = p.to_ising(p.default_penalty() if penalty is None else penalty)
        ans = QAOAAnsatz(H, reps=reps)
    else:
        raise ValueError(variant)
    return ans.decompose(reps=3), H


# ---------- qaoa.py ----------
def linear_ramp_init(reps: int, delta: float = 0.75) -> np.ndarray:
    # QAOAAnsatz parameter order: β[0..p-1], γ[0..p-1] (sorted by name)
    l = (np.arange(reps) + 0.5) / reps
    return np.concatenate([(1 - l) * delta, l * delta])


def optimize(ansatz, H, restarts=8, maxiter=300, seed=0):
    rng = np.random.default_rng(seed)
    est = StatevectorEstimator()

    def energy(theta):
        return float(est.run([(ansatz, H, theta)]).result()[0].data.evs)

    reps = ansatz.num_parameters // 2
    starts = [linear_ramp_init(reps)] + [
        rng.uniform(-np.pi / 2, np.pi / 2, ansatz.num_parameters) for _ in range(restarts - 1)
    ]
    best = None
    for x0 in starts:
        r = minimize(energy, x0, method="COBYLA", options={"maxiter": maxiter})
        if best is None or r.fun < best.fun:
            best = r
    return best


def sample(ansatz, params, sampler=None, shots=4096, seed=0):
    sampler = sampler or StatevectorSampler(seed=seed)
    circ = ansatz.assign_parameters(params)
    circ.measure_all()
    return sampler.run([circ], shots=shots).result()[0].data.meas.get_counts()


# ---------- metrics.py / noise.py ----------
def evaluate_counts(counts, p: PortfolioProblem):
    feas = p.feasible_set()
    costs = np.array([p.cost(x) for x in feas])
    best = feas[costs.argmin()]
    cmin, cmax = costs.min(), costs.max()
    shots = sum(counts.values())
    nf = no = 0
    ec = 0.0
    top = (-1, None)
    for b, c in counts.items():
        x = bitstring_to_x(b)
        if x.sum() == p.k:
            nf += c
            ec += c * p.cost(x)
            top = max(top, (c, b), key=lambda t: t[0])
            if (x == best).all():
                no += c
    return {
        "p_feasible": nf / shots,
        "p_optimal": no / shots,
        "p_optimal_postselected": no / nf if nf else 0.0,
        "approx_ratio": float((cmax - ec / nf) / (cmax - cmin)) if nf else 0.0,
        "top1_is_optimal": bool(top[1] is not None and (bitstring_to_x(top[1]) == best).all()),
        "p_random": 1 / len(feas),
        "shots": shots,
    }


def postselect(counts, k):
    return {b: c for b, c in counts.items() if b.count("1") == k}


def readout_mitigate(counts, cal_mats):
    """cal_mats[i] = 2x2 matrix M[measured, prepared] for qubit i. Tensored inverse."""
    n = len(cal_mats)
    shots = sum(counts.values())
    vec = np.zeros(2**n)
    for b, c in counts.items():
        vec[int(b, 2)] = c / shots
    t = vec.reshape([2] * n)  # axis 0 = leftmost char = qubit n-1
    for i, M in enumerate(cal_mats):
        axis = n - 1 - i
        t = np.moveaxis(np.tensordot(np.linalg.inv(M), t, axes=([1], [axis])), 0, axis)
    v = np.clip(t.reshape(-1), 0, None)
    v /= v.sum()
    return {format(i, f"0{n}b"): float(x) for i, x in enumerate(v) if x > 1e-12}
```

## Noisy simulation and hardware snippets

```python
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeTorino

backend = FakeTorino()
circ = ansatz.assign_parameters(params); circ.measure_all()
tc = transpile(circ, backend, optimization_level=3, seed_transpiler=0)
twoq = sum(v for g, v in tc.count_ops().items() if g in ("cz", "ecr", "cx"))
counts = AerSimulator.from_backend(backend).run(tc, shots=8192, seed_simulator=0).result().get_counts()
layout = tc.layout.final_index_layout()          # physical qubit for each virtual qubit
```

Readout calibration on the same physical qubits: build two n-qubit circuits (all-0 and all-X), transpile them with
`initial_layout=layout`, run them, and estimate per-qubit `M[i] = [[P(0|0), P(0|1)], [P(1|0), P(1|1)]]`
from the marginals. Then call `readout_mitigate(counts, M)`.

```python
# hardware.py: submit (Open Plan supports job and batch mode; sessions need a paid plan)
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

service = QiskitRuntimeService()                      # reads ~/.qiskit/qiskit-ibm.json
backend = service.least_busy(operational=True, simulator=False, min_num_qubits=8)
pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=0)
isa = pm.run(circ)                                    # circ already has measurements
sampler = Sampler(mode=backend)
sampler.options.default_shots = 8192
sampler.options.dynamical_decoupling.enable = True
sampler.options.dynamical_decoupling.sequence_type = "XY4"
sampler.options.twirling.enable_gates = True
sampler.options.twirling.enable_measure = True
job = sampler.run([isa, *isa_calibration_circuits])  # PUB 0 = QAOA, PUBs 1–2 = readout calibration
print(job.job_id())                                   # save to results/hardware/

# collect (can be a different day/process)
job = service.job(job_id)
res = job.result()
counts = res[0].data.meas.get_counts()
```
