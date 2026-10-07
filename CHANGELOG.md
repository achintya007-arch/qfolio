# Changelog
All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: SemVer.

## [Unreleased]
### Added
- Project documentation: spec, architecture, methodology, verified implementation notes, benchmark protocol,
  hardware runbook, CI/CD and deployment guide, testing strategy, rubric map, business brief, demo script, ADRs.
- `data`, `problem`, `classical`, `config`, `io` modules; cached `data/prices.csv` (10 NSE tickers,
  2023-01-02 → 2025-12-31, 740 days); `scripts/fetch_data.py`, `scripts/show_instance.py`; tests incl. AC1, AC2.
- CI (lint, tests on Python 3.11/3.12, notebook smoke test, secret scan), GitHub Pages report and release workflows.
- IBM hardware runner: `hardware.py` and `scripts/run_hardware.py` with `--dry-run` (FakeTorino,
  same SamplerV2 path) / `--submit` / `--status` / `--collect`; readout calibration and mitigation.

### Fixed
- Hardware job `db3attimb58s7387dsd0` (ibm_kingston) failed with "Error code 3211; Job not valid.
  Options field seed_simulator is not valid for this backend". Simulator options are now sent only to
  fake backends, with a unit test; `--status` prints the job's error message on failure. Record:
  `results/hardware/failed_db3attimb58s7387dsd0.json`; resubmitted as `db3b1bimb58s7387e0jg`.

## [1.0.0] - 2026-10-08
<!-- Fill at submission: what was submitted, headline numbers, hardware job ID. -->
