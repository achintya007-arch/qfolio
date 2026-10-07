# CLAUDE.md: instructions for Claude Code in this repo

You are helping **Achintya** build a hackathon submission for **Qiskit Fall Fest 2026, Industry Track I2: Portfolio Optimizer**.
It is an **individual** event. Achintya must be able to explain every line in a 3-minute live demo, so keep the code simple and readable and explain non-obvious choices in comments.

## Hard deadline
**Thu 8 Oct 2026, 14:00 IST.** (The event deck says both 14:00 and 15:00; we plan for 14:00.) Late = disqualified.
Follow `docs/00_PLAN.md`. If a phase runs over, cut scope using the **"cut list"** in that plan. Never skip tests or the README.

## Source of truth
Read these before writing code, in this order:
1. `docs/01_SPEC.md`: what to build and the acceptance criteria
2. `docs/02_ARCHITECTURE.md`: module boundaries and function signatures
3. `docs/04_IMPLEMENTATION_NOTES.md`: **verified** Qiskit 2.x reference code. Reuse it rather than reinventing it. It encodes bugs we already hit.
4. `docs/05_BENCHMARK_PROTOCOL.md`: fairness rules for every comparison

If the code and the docs disagree, stop and ask. When a decision changes, update the doc *in the same commit*.

## Non-negotiable rules
- **Qiskit 2.x only**: `qiskit>=2.0`, V2 primitives (`StatevectorEstimator`, `StatevectorSampler`, `qiskit_ibm_runtime.SamplerV2`). Do not use `qiskit.execute`, `Aer.get_backend` or V1 primitives. Do not depend on `qiskit-algorithms` or `qiskit-optimization`: we implement QAOA ourselves because it scores higher on "Qiskit implementation" and avoids version breakage.
- **Bit order:** Qiskit is little-endian. Always convert with `bitstring_to_x()` from `qportfolio.problem`. Never hand-reverse strings elsewhere.
- **Honesty:** never write "quantum advantage", "outperforms classical" or "speed-up". Report P(optimal), approximation ratio, feasibility and wall time *next to* the classical baselines.
- **Reproducibility:** every random thing takes a `seed` from `configs/default.yaml`. Results are written to `results/*.json` with the config hash, package versions and timestamp.
- **No network in tests/CI.** Data comes from `data/prices.csv` (committed). Only `scripts/fetch_data.py` touches the network.
- **Secrets:** never print, log or commit an IBM token. The token lives only in `~/.qiskit/qiskit-ibm.json` (via `QiskitRuntimeService.save_account`) or in the `QISKIT_IBM_TOKEN` env var. `.env` is git-ignored.
- **Public/synthetic data only.**

## Commands
```bash
make setup        # venv + pip install -r requirements-dev.txt + pre-commit install
make lint         # ruff check + ruff format --check
make test         # pytest -q (fast; < 60 s)
make test-all     # includes @pytest.mark.slow
make reproduce    # full pipeline → results/ and results/figures/
make notebook     # execute notebooks/qfolio.ipynb in place
make report       # build site/ (HTML report) locally
make app          # streamlit run app/streamlit_app.py
```
On Windows (no `make`), use `.\tasks.ps1 <target>` with the same target names, e.g. `.\tasks.ps1 lint`, `.\tasks.ps1 test`.
It always runs `.venv\Scripts\python`.

## Code style
- Python 3.11+, type hints on public functions, NumPy-style docstrings with a one-line summary.
- `ruff` (line length 100) is the only formatter and linter.
- Pure functions in `src/qportfolio/`; I/O only in `scripts/` and `app/`.
- Small modules (< ~250 lines). No classes where a function will do, except the `PortfolioProblem` dataclass.
- Plots: matplotlib, one function per figure in `viz.py`, saved as both PNG (dpi 200) and SVG.

## Git workflow
- Commit after every green step. Use Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, `chore:`).
- Work on `main` (solo hackathon), but **CI must be green before tagging**.
- Commit early and often: the history is evidence that all code was written after the announcement.
- Final submission = annotated tag `v1.0.0` plus a GitHub Release with the brief PDF and slides attached.

## Definition of done (per phase)
Code + tests pass + docs updated + `make lint test` green + committed + pushed + CI green.

## When unsure
Prefer the simpler option and leave a `# NOTE(achintya): …` comment explaining the trade-off, so he can talk about it in the demo.
