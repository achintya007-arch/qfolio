# Changelog
All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: SemVer.

## [Unreleased]

## [1.0.0] - 2026-10-08
First submitted version (Qiskit Fall Fest 2026, Track I2).

### Added
- Project documentation: spec, architecture, methodology, verified implementation notes, benchmark protocol,
  hardware runbook, CI/CD and deployment guide, testing strategy, rubric map, business brief, demo script, ADRs.
- `data`, `problem`, `classical`, `config`, `io` modules; cached `data/prices.csv` (10 NSE tickers,
  2023-01-02 → 2025-12-31, 740 days); `scripts/fetch_data.py`, `scripts/show_instance.py`; tests incl. AC1, AC2.
- CI (lint, tests on Python 3.11/3.12, notebook smoke test, secret scan), GitHub Pages report and release workflows.
- IBM hardware runner: `hardware.py` and `scripts/run_hardware.py` with `--dry-run` (FakeTorino,
  same SamplerV2 path) / `--submit` / `--status` / `--collect`; readout calibration and mitigation.
- XY-QAOA (Dicke initial state + ring XY mixer) and penalty-QAOA (X mixer) implemented directly on
  Qiskit 2.x V2 primitives; `StatevectorEstimator` + COBYLA training, 8 restarts.
- Multi-instance benchmark (`scripts/run_benchmark.py`): 1 real NSE instance + 24 robustness instances
  (3 of 6) against brute force, greedy and simulated annealing → `results/benchmark.json`.
- Noise study (`noise.py`, `scripts/run_noisy.py`) on FakeTorino and FakeFez: transpile table, symmetry
  post-selection, readout mitigation → `results/noisy.json`.
- Figures (`viz.py`, `scripts/make_figures.py`), submission notebook, Streamlit app (4 tabs), Pages report
  and landing page.
- Story deliverables: one-page business brief (MD + PDF), 3-slide deck with speaker notes
  (`scripts/make_slides.py`), demo script, `scripts/export_pdf.py`.
- `scripts/fill_readme.py`: README results tables generated from `results/*.json` (with a test that the
  committed README matches the JSON).
- IBM Quantum dashboard screenshots for job `db3b1bimb58s7387e0jg` in `results/hardware/`.

### Fixed
- Hardware job `db3attimb58s7387dsd0` (ibm_kingston) failed with "Error code 3211; Job not valid.
  Options field seed_simulator is not valid for this backend". Simulator options are now sent only to
  fake backends, with a unit test; `--status` prints the job's error message on failure. Record:
  `results/hardware/failed_db3attimb58s7387dsd0.json`; resubmitted as `db3b1bimb58s7387e0jg`.

### Results (all from `results/*.json`)
- 24 robustness instances, p = 2: XY-QAOA P(optimal) 0.34 ± 0.16 vs 0.05 random, 100% valid baskets;
  simulated annealing 0.36 ± 0.08; penalty-QAOA 0.04 (chance level), 75% valid.
- Real NSE instance (best two baskets 1.4% apart): XY-QAOA P(top-2) 0.37 vs 0.10 random, approximation
  ratio 0.84 vs 0.52.
- Real hardware, `ibm_kingston`, job `db3b1bimb58s7387e0jg` (4 assets, k = 2, p = 2, 8192 shots):
  P(optimal) 0.51 raw → 0.65 post-selected vs 0.17 random; top answer = true optimum.
- No quantum-advantage claim: brute force solves these sizes in under a millisecond.
