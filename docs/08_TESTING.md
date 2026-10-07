# 08 · Testing strategy

Goal: every scientific claim in the README is backed by a test or by a reproducible JSON.

| Test file | Test | Proves | Speed |
|---|---|---|---|
| `test_problem.py` | `test_qubo_matches_objective_all_bitstrings` | AC1: QUBO + const = C(x) + λ(Σx−k)² for all 2ⁿ x | fast |
| | `test_ising_diagonal_matches_qubo` | AC2: H's diagonal is an affine map of the QUBO energies | fast |
| | `test_bitstring_roundtrip_little_endian` | bit-order bugs are impossible | fast |
| | `test_feasible_set_size` | len = C(n,k) | fast |
| `test_classical.py` | `test_brute_force_matches_exhaustive` | baseline is correct | fast |
| | `test_sa_finds_optimum_small` | SA is a credible competitor | fast |
| | `test_greedy_returns_feasible` | | fast |
| `test_circuits.py` | `test_dicke_uniform_weight_k` (parametrised over (4,2),(5,2),(6,3)) | AC3 | fast |
| | `test_xy_mixer_conserves_weight` | AC4: random β, statevector stays in the weight-k subspace | fast |
| | `test_qaoa_parameter_order` | β before γ | fast |
| `test_qaoa.py` | `test_xy_qaoa_beats_random_default_instance` | AC5 (restated): P(feasible) = 1, P(opt) > random | slow (≈ 20 s) |
| | `test_xy_qaoa_top1_is_optimal_default_instance` | original AC5; strict `xfail` (near-degenerate optimum) | slow |
| | `test_penalty_vs_xy_feasibility` | XY P(feasible) = 1, penalty < 1 | slow |
| `test_metrics.py` | hand-built counts → known P(opt), AR | metric definitions | fast |
| `test_noise.py` | `test_readout_mitigation_recovers_ideal` | synthetic flip noise → ideal within 1e-3 | fast |
| | `test_postselect_drops_wrong_weight` | | fast |
| | `test_transpile_report_columns` (FakeTorino) | | fast |
| `test_data.py` | cached CSV loads; μ, Σ shapes; Σ symmetric PSD | data sanity | fast |

Markers: `@pytest.mark.slow` excluded from `make test` and included in `make test-all` and CI's nightly-style job.
Coverage target: ≥ 85% of `src/qportfolio` (excluding `hardware.py`, which is network-bound and checked by a dry-run test that mocks `QiskitRuntimeService`).
Notebook: `pytest --nbmake notebooks/` with `QFOLIO_FAST=1` (fewer restarts and shots) runs in CI.
