# 03 · Methodology

## 1. Financial model
Daily adjusted close prices P_t → log returns r_t = ln(P_t / P_{t−1}).
Annualised: **μ = 252 · mean(r)**, **Σ = 252 · cov(r)**.

Select a binary vector x ∈ {0,1}ⁿ with exactly k ones (equal-weight basket). Minimise

$$ C(x) = q\,x^\top \Sigma x \;-\; \mu^\top x \qquad \text{s.t.}\quad \textstyle\sum_i x_i = k $$

q is the risk-aversion knob (0.25 = growth, 0.5 = balanced, 1.0 = conservative).
*Why equal weights:* it keeps the problem binary and matches how model baskets are sold to retail clients. The scaling factor 1/k is constant, so it does not change the arg-min.

## 2. QUBO
Penalty form (needed for penalty-QAOA and simulated annealing):

$$ C_\lambda(x) = x^\top Q x + c,\quad Q = q\Sigma - \mathrm{diag}(\mu) + \lambda(\mathbf{1}\mathbf{1}^\top - I) + \lambda(1-2k)I,\quad c=\lambda k^2 $$

(using x_i² = x_i). The default λ is the feasible-cost range (max − min over C(n,k) feasible strings); `default_penalty()` documents this. **The XY variant uses λ = 0**, because feasibility is enforced by the circuit.

## 3. Ising mapping
x_i = (1 − z_i)/2, z_i ∈ {±1} ↔ Pauli Z_i:

$$ H = \sum_{i<j} J_{ij} Z_i Z_j + \sum_i h_i Z_i + \text{const},\quad J_{ij} = \tfrac{Q_{ij}+Q_{ji}}{4},\quad h_i = -\tfrac{Q_{ii}}{2} - \sum_{j\neq i}\tfrac{Q_{ij}+Q_{ji}}{4} $$

The coefficients are normalised by max|Q| so the optimiser sees angles of order 1. The arg-min is unchanged.

## 4. QAOA variants

**(a) Penalty-QAOA (textbook).** |+⟩^⊗n, cost layer e^{−iγH_λ}, mixer e^{−iβΣX_i}. It searches all 2ⁿ strings; infeasible strings are discouraged only by λ.

**(b) Constraint-preserving XY-QAOA (ours).** Following Hadfield et al. (2019), *Quantum Approximate Optimization Algorithm and the Quantum Alternating Operator Ansatz*:
- **Initial state:** the Dicke state |D^n_k⟩, a uniform superposition over all C(n,k) valid portfolios. Prepared deterministically with the Bärtschi & Eidenbenz (2019) circuit (*Deterministic Preparation of Dicke States*).
- **Mixer:** the ring XY mixer Σ_{⟨i,i+1⟩} (X_iX_{i+1} + Y_iY_{i+1})/2. It swaps a 1 and a 0 between neighbours, so it **preserves Hamming weight**. Implemented as `XXPlusYYGate(2β)` on even edges and then odd edges ("parity ring"). Each gate conserves weight exactly.
- **Cost:** H with λ = 0 (pure objective).
- **Consequence:** the ideal circuit never leaves the feasible subspace (dimension C(n,k) instead of 2ⁿ). On hardware, any sample with the wrong weight *must* be an error, which gives us free error detection (§6).

**Why (b) beats (a), in plain words:** with a penalty, most of the optimiser's effort goes into learning "pick k assets". The penalty also squashes the real cost differences into a small part of the energy scale. With XY, every amplitude already sits on a valid portfolio, so the optimiser only has to learn "which valid portfolio is best".

**Parameter optimisation:** exact expectation ⟨H⟩ via `StatevectorEstimator`, COBYLA, 8 restarts (one is a linear-ramp warm start γ_l = (l/p)·Δ, β_l = (1 − l/p)·Δ), and keep the best. Parameters are trained on the simulator and **reused on hardware** (no on-device training, which saves QPU time).

## 5. Metrics (computed on samples)
| Metric | Definition | Why |
|---|---|---|
| P(feasible) | share of shots with Σx = k | valid baskets |
| P(optimal) | share of shots = brute-force optimum | headline: compare to random 1/C(n,k) |
| P(opt \| post-selected) | P(optimal) among feasible shots | the symmetry-verified number |
| Approximation ratio | (C_max − E[C \| feasible]) / (C_max − C_min) | 1 = always optimal, 0 = always worst; random ≈ 0.5 |
| Top-1 is optimal | most frequent feasible bitstring == optimum | what a user would actually pick |
| Wall time / evaluations | timing for all methods | honesty about cost |

## 6. Noise-aware engineering
1. **Transpilation study:** levels 0–3 on the target backend → depth, 2-qubit gate count and estimated fidelity (product of the gate fidelities from the backend's error rates). Pick the best.
2. **Layout:** let the transpiler choose (`optimization_level=3`, `seed_transpiler` fixed); report the physical qubits used.
3. **Symmetry post-selection:** discard shots with Σx ≠ k. This is valid *only* because the XY circuit conserves weight (AC4). For penalty-QAOA it is just filtering, and we say so.
4. **Readout mitigation:** per-qubit 2×2 confusion matrices from two calibration circuits (|0…0⟩, |1…1⟩), tensored inverse, negative quasi-probabilities clipped and renormalised.
5. **Hardware only:** `SamplerV2` options: dynamical decoupling (XY4) on, Pauli twirling of gates + measurements on.
6. Report **raw → post-selected → post-selected + readout-mitigated** side by side. Never report only the best number.

## 7. Scaling and what would need to be true
- Feasible space C(n,k): 20 at (6,3), 184 756 at (20,10), ~10²⁹ at (100,50). Brute force dies around n ≈ 40; good heuristics (SA, MIQP solvers like Gurobi) handle hundreds of assets today.
- For QAOA to matter, it would need **(i)** fault-tolerant or much lower-error hardware to reach the depth p ≫ 1 that larger n needs, **(ii)** evidence that P(optimal) decays more slowly than classical heuristics' success probability on hard instances, and **(iii)** a cheap way to set parameters (transfer/concentration) at scale.
- Our contribution is **methodological**: building constraints into the circuit is necessary even at toy scale (penalty-QAOA performs at chance), and the same symmetry also gives free error detection on hardware.

## References
1. H. Markowitz, "Portfolio Selection," *J. Finance* 7(1), 1952.
2. E. Farhi, J. Goldstone, S. Gutmann, "A Quantum Approximate Optimization Algorithm," arXiv:1411.4028, 2014.
3. S. Hadfield et al., "From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz," *Algorithms* 12(2):34, 2019.
4. A. Bärtschi, S. Eidenbenz, "Deterministic Preparation of Dicke States," FCT 2019, arXiv:1904.07358.
5. S. Hodson et al., "Portfolio rebalancing experiments using the Quantum Alternating Operator Ansatz," arXiv:1911.05296, 2019.
6. P. Barkoutsos et al., "Improving Variational Quantum Optimization using CVaR," *Quantum* 4, 256, 2020.
