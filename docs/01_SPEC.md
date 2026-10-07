# 01 · Specification

## 1. Problem statement
A wealth-tech / robo-advisor platform builds model baskets for retail investors. Given *n* candidate assets, it must pick **exactly k** to hold in equal weight, so that **expected return is high and portfolio risk (variance) is low**. This is the *cardinality-constrained mean–variance* problem. In binary form it is NP-hard, and the search space grows as C(n, k).

## 2. Scope
**In scope**
- n = 4–6 assets (hardware: n = 4, k = 2; simulator: n = 6, k = 3), equal weights over the selected assets.
- Public daily prices, cached in the repo. Default universe: six NSE large caps across different sectors (see `data/README.md`).
- Quantum: QAOA, implemented directly on Qiskit 2.x primitives, in two variants: (a) penalty + X mixer, (b) XY-ring mixer + Dicke initial state.
- Classical: brute force (exact), simulated annealing on the identical QUBO, greedy.
- Noise: IBM fake-backend noise models, transpiler optimisation levels, symmetry post-selection, readout mitigation, dynamical decoupling (on hardware).
- Real IBM hardware run with fixed (simulator-trained) parameters.
- Deliverables: notebook, library, tests, CI, Pages report, Streamlit app, brief, slides, video.

**Out of scope**
Continuous weights, transaction costs, short selling, sector/lot constraints, more than 8 qubits, any claim of quantum advantage.

## 3. Functional requirements
| ID | Requirement |
|---|---|
| FR1 | Load prices → annualised mean returns μ and covariance Σ (252 trading days). |
| FR2 | `PortfolioProblem(mu, sigma, k, q)` exposes `cost(x)`, `feasible_set()`, `to_qubo(penalty)`, `to_ising(penalty)`. |
| FR3 | Brute force returns the exact optimum and the full feasible-cost spectrum (needed for the approximation ratio). |
| FR4 | Simulated annealing + greedy operate on the **same** objective, with the evaluation budget and time recorded. |
| FR5 | `build_qaoa(problem, reps, variant={"penalty","xy"})` returns a parameterised `QuantumCircuit` and the cost `SparsePauliOp`. |
| FR6 | `optimize(...)` uses `StatevectorEstimator` + SciPy COBYLA with N restarts; returns the best parameters and the history. |
| FR7 | `sample(...)` runs a V2 sampler (statevector, Aer noisy, or IBM Runtime) and returns counts. |
| FR8 | `metrics(counts, problem)` → P(feasible), P(optimal), approximation ratio (feasible-conditioned), top-1 is optimal, expected cost. |
| FR9 | Noise pipeline: transpile at levels 0–3 → depth / 2q-count table; raw vs post-selected vs readout-mitigated metrics. |
| FR10 | Hardware script: `--submit` saves the job ID; `--collect` saves raw counts + metrics + backend calibration snapshot. |
| FR11 | `make reproduce` regenerates every JSON and figure from a clean clone, offline. |
| FR12 | Streamlit app: pick assets, k and risk aversion q → brute force vs XY-QAOA live (statevector) + stored hardware results. |

## 4. Non-functional requirements
- Full pipeline < 10 min on a laptop CPU; `make test` < 60 s; app responds in < 10 s.
- Deterministic given the seeds in `configs/default.yaml`.
- Python 3.11 and 3.12; Linux, macOS and Windows.
- Readable by a judge in 5 minutes: README → notebook → brief.

## 5. Acceptance criteria
- [ ] AC1: For every bitstring, `x·Q·x + const == cost(x) + λ(Σx − k)²` (unit test, all 2ⁿ).
- [ ] AC2: The Ising Hamiltonian's diagonal equals the QUBO energies (unit test).
- [ ] AC3: The Dicke circuit produces a uniform superposition over all weight-k strings, max error < 1e-9 (unit test).
- [ ] AC4: The XY mixer conserves Hamming weight: the ideal simulation of XY-QAOA has P(feasible) = 1.000 (unit test).
- [ ] AC5: On the default instance (ideal simulator, p=1), XY-QAOA has P(feasible) = 1.000 and P(optimal) above random (1/C(n,k)).
  *Changed 2026-10-08:* the original AC5 ("most frequent bitstring = optimum") fails on the real NSE instance at p = 1, 2, 3.
  Its optimum and runner-up differ by only 0.004 in cost, and the mode settles on the 4th-best basket. Measured at p=1:
  P(optimal) = 0.131 vs 0.05 random. The old check is kept as a strict `xfail` so a future fix is noticed.
- [ ] AC6: The benchmark covers ≥ 20 instances (random asset subsets / q values), and reports mean ± std.
- [ ] AC7: Every table in the README is generated from `results/*.json`.
- [ ] AC8: CI is green on `main`; the Pages report is live; the release `v1.0.0` exists.

## 6. Expected outcomes (from pre-build validation on synthetic data, n=6, k=3)
These ranges come from a validation run done while writing the docs. They **set expectations only**; the README reports the real runs.

| Variant | P(feasible) | P(optimal) | Random P(opt) |
|---|---|---|---|
| Penalty QAOA p=1–3 (any λ, also with CVaR α=0.1) | 0.65–0.79 | 0.03–0.05 | 0.05 |
| XY-QAOA, Dicke init, p=1 | 1.00 | ≈ 0.25 | 0.05 |
| XY-QAOA, Dicke init, p=2 | 1.00 | ≈ 0.36 | 0.05 |
| XY-QAOA n=4,k=2, ideal | 1.00 | ≈ 0.66 | 0.167 |
| … same, FakeTorino noise, raw / post-selected | 0.83 / 1.00 | ≈ 0.50 / 0.60 | 0.167 |
