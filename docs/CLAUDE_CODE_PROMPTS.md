# Claude Code prompts, phase by phase

How to use: open a terminal in the repo folder, run `claude`, and paste one prompt per phase. Wait for green tests and a commit before moving on.
Each prompt is self-contained because Claude Code also reads `CLAUDE.md` automatically.
Tip: start each phase with `/clear` to keep the context small and quick.

---

### P0 · Bootstrap (17:00)
```
Environment: Windows, Python 3.12 venv at .venv. Always run Python as .venv\Scripts\python
(and pip as .venv\Scripts\python -m pip). There is no make on Windows, so also create tasks.ps1
with the same targets as the Makefile and use those commands from now on.
Read CLAUDE.md and every file in docs/. Then:
1. Create the package skeleton exactly as in docs/02_ARCHITECTURE.md (modules with docstrings and the public
   signatures raising NotImplementedError) and tests/test_smoke.py (imports the package). The Makefile,
   configs/default.yaml, pyproject.toml, requirements*.txt and .github/workflows already exist; do not rewrite
   them, only fix them if they are broken. Create placeholder notebooks/qfolio.ipynb and scripts/build_report.sh
   so the CI and Pages workflows pass, and src/qportfolio/demo.py printing "checkpoint: TODO".
2. Make sure `make lint` and `make test` pass.
3. git init (if needed), commit "chore: bootstrap repo with docs, CI and skeleton", then run the gh commands in
   docs/07_CI_CD_AND_DEPLOYMENT.md §1 to create the PUBLIC repo achintya007-arch/qfolio and push.
4. Watch the CI run with `gh run watch` and fix anything red.
Do not implement any algorithm yet.
```

### P1 · Data, problem, classical baselines (17:30)
```
Implement src/qportfolio/data.py, problem.py, classical.py and io.py following docs/02 (signatures) and
docs/04 (reference code: reuse it). Then:
- scripts/fetch_data.py: download adjusted closes for the 10-ticker universe in data/README.md
  (2023-01-01 → 2025-12-31) with yfinance and write data/prices.csv. Run it once now and commit the CSV.
- tests from docs/08 for problem, classical and data (AC1, AC2 included).
- Print, for the default instance: μ, Σ, all 20 feasible baskets sorted by cost, and the optimum.
Commit after tests are green.
```

### P2 · Circuits and QAOA: the checkpoint artefact (19:00)
```
Implement circuits.py, qaoa.py and metrics.py from docs/04 (reuse the verified code, keeping the XY mixer as a
circuit of XXPlusYYGate, NOT a SparsePauliOp; see pitfall #1). Add the tests for AC3, AC4, AC5 and the
parameter-order test. Create src/qportfolio/demo.py so that `python -m qportfolio.demo` builds the default
instance, draws the p=1 XY-QAOA circuit (text), optimises it, samples it, and prints a table:
method | P(feasible) | P(optimal) | top-1 basket | brute-force optimum. Include penalty-QAOA p=1 for contrast.
Commit "feat: XY-QAOA with Dicke init; checkpoint demo".
```

### P3 · Benchmark (21:00)
```
Implement scripts/run_benchmark.py per docs/05_BENCHMARK_PROTOCOL.md: headline real-data instance plus 20+
robustness instances, methods = random (analytic), brute force, greedy, simulated annealing, penalty-QAOA
p=1,2, XY-QAOA p=1,2,3. Headline metrics: P(optimal), approximation ratio and P(top-2 baskets), side by
side (add `p_top2` to metrics.evaluate_counts + test). Save results/benchmark.json using the schema in docs/02.
Then implement viz.py and
scripts/make_figures.py for figures 1, 2, 3, 6 and 7 from docs/05 §7 (PNG + SVG, readable at slide size,
colour-blind-safe palette, every axis labelled with units). Respect QFOLIO_FAST=1 (fewer instances and
restarts) so CI stays under 5 minutes. Add `make reproduce`. Commit.
```

### P4 · Noise-aware engineering (22:30)
```
Implement noise.py and scripts/run_noisy.py per docs/03 §6 and docs/04 (noisy snippets):
hardware instance (4 assets, k=2), XY-QAOA p=1 and p=2 with simulator-trained params, on FakeTorino and
FakeBrisbane: transpile report for levels 0-3 (depth, 2q count, estimated fidelity), then raw → post-selected
→ post-selected + readout-mitigated metrics. Save results/noisy.json and figures 4 and 5. Add tests from docs/08
for noise.py. Commit.
```

### P7a · Submit the hardware job (23:30). **You run the final command yourself.**
```
Implement hardware.py and scripts/run_hardware.py with --submit / --status / --collect exactly as in
docs/06_HARDWARE_RUNBOOK.md and docs/04. Never read, print or ask for my token; assume it is already saved via
QiskitRuntimeService.save_account. Add a --dry-run flag that uses FakeTorino through the same SamplerV2 code
path, and a unit test using --dry-run. Run the dry run, then STOP and tell me the exact command to submit.
```
Then in your own terminal: `python scripts/run_hardware.py --submit`, then commit `results/hardware/pending.json`.

### P7b · Collect (Day 2, 07:30)
```
Run `python scripts/run_hardware.py --collect`, regenerate figures, and add the hardware row to the results.
Summarise the raw vs post-selected vs mitigated numbers for me in plain words. Commit.
```

### P5 · Notebook (08:00)
```
Create notebooks/qfolio.ipynb as the submission narrative, following the "Predict → Build → Benchmark →
Explain" structure: 1 Business problem, 2 Data, 3 Formulation (QUBO/Ising, short maths from docs/03),
4 Classical baselines, 5 Penalty-QAOA and why it fails, 6 XY-QAOA (draw the Dicke + mixer circuits),
7 Benchmark results, 8 Noise-aware + hardware, 9 Limits and next steps. The notebook imports from qportfolio
(no copy-pasted logic), loads the results JSON when present, and recomputes when QFOLIO_RECOMPUTE=1.
Markdown cells are short and plain-English. It must run top-to-bottom via `make notebook`. Commit.
```

### P6 · App and deployment (09:30)
```
Build app/streamlit_app.py with the four tabs in docs/07 §3, using qportfolio functions and @st.cache_data.
Then build scripts/build_report.sh and the Pages landing page (docs/07 §2). Run `make app` and `make report`
locally and fix any issues. Push and confirm pages.yml deploys. Give me the exact clicks to deploy on
share.streamlit.io. Commit.
```

### P8 · Story (10:30)
```
Fill docs/BUSINESS_BRIEF.md from results/*.json (replace every ⟨…⟩; find and cite one real Indian
wealth-tech market statistic). Keep it to ONE page; export to docs/BUSINESS_BRIEF.pdf.
Implement scripts/fill_readme.py and run it so the README results table comes from JSON.
Update DEMO_SCRIPT.md with the final numbers. Commit.
```

### P9 · Release (12:00)
```
Final check: fresh clone into /tmp, create a venv, pip install -r requirements.txt, make test, make reproduce
(QFOLIO_FAST=1), and make sure there are no ⟨…⟩ placeholders left anywhere (grep). Check that every README link
resolves. Update CHANGELOG.md, then tag v1.0.0 and push. Confirm the release workflow created the GitHub Release.
```
