# 00 · Build plan (Day 1 evening → Day 2 14:00 IST)

All times IST. Each phase has a matching copy-paste prompt in [CLAUDE_CODE_PROMPTS.md](CLAUDE_CODE_PROMPTS.md).

## Timeline

| When | Phase | Output | Done when |
|---|---|---|---|
| **Wed 7 Oct** 17:00–17:30 | **P0 Bootstrap** | Public repo, docs pushed, CI skeleton green | Badge on README is green |
| 17:30–19:00 | **P1 Problem + classical** | `data.py`, `problem.py`, `classical.py`, cached `data/prices.csv`, tests | QUBO energy == objective for all 2ⁿ bitstrings (test) |
| 19:00–20:30 | **P2 Circuits + QAOA** ✅ *checkpoint artefact* | `circuits.py`, `qaoa.py`, `metrics.py`, tests | XY-QAOA finds the brute-force optimum as its top sample |
| 20:30–21:00 | Dinner | | |
| 21:00–22:30 | **P3 Benchmark** | `scripts/run_benchmark.py`, `results/benchmark.json`, headline figures | Multi-instance table + `headline.png` |
| 22:30–23:30 | **P4 Noise-aware** | `noise.py`, `scripts/run_noisy.py`, transpile/mitigation comparison | Raw vs post-selected vs mitigated on ≥ 1 fake backend |
| **23:30** | **P7a Submit hardware job** ⚡ | `scripts/run_hardware.py --submit` | Job ID saved in `results/hardware/` (the queue runs overnight) |
| 23:30–00:15 | Commit, push, sleep | | CI green |
| **Thu 8 Oct** 07:30–08:00 | **P7b Collect hardware** | `scripts/run_hardware.py --collect` | Counts + metrics in `results/hardware/` |
| 08:00–09:30 | **P5 Notebook** | `notebooks/qfolio.ipynb`, executed end-to-end | `make notebook` passes from a clean clone |
| 09:30–10:30 | **P6 App + deploy** | Streamlit app live, Pages report live | Both URLs open in an incognito window |
| 10:30–12:00 | **P8 Story** | Business brief (PDF), 3 slides, 2-min video | Video uploaded (unlisted), links in README |
| 12:00–12:45 | **P9 Polish + release** | README results filled, `v1.0.0` tag, Release | Fresh-clone rerun works |
| **12:45–13:30** | **Buffer + SUBMIT** | Submission form filled | Submitted **before 13:30** |
| 14:00 | Deadline | | |

**Day 2 checkpoint** (the time is announced by the organisers). Have this ready:
> *One-line plan:* "Cardinality-constrained portfolio selection with QAOA using an XY-mixer + Dicke state so every sample is a valid portfolio, benchmarked against brute force and simulated annealing, with noise-aware runs on IBM hardware."
> *First working circuit:* `python -m qportfolio.demo` prints the circuit and shows that the top sample = the brute-force optimum.

## Cut list (drop from the bottom up if behind)
1. ~~Out-of-sample backtest (2025 hold-out)~~ stretch
2. ~~CVaR objective variant~~ stretch
3. ~~Second fake backend~~
4. ~~Streamlit app~~ → keep the Pages report only (still counts as deployment)
5. ~~Penalty sweep figure~~ → keep one penalty-QAOA row in the table
6. **Never cut:** brute-force baseline, simulated annealing, XY vs penalty comparison, README, brief, tests, CI, demo video/slides.

## Risks and mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| IBM queue too long | Medium | Submit at 23:30 Day 1; hardware is a bonus, so if no result arrives, report the noisy-sim result and the pending job ID |
| Open Plan time exhausted | Low | Optimise parameters on the simulator; hardware runs fixed parameters only (≈ 3 circuits × 4k shots, a few seconds of QPU time) |
| yfinance fails | Medium | Data is fetched once and committed; synthetic fallback in `data.py` |
| Optimiser gets stuck in a bad local minimum | Medium | 8 random restarts + linear-ramp warm start (see doc 04) |
| Streamlit Cloud build fails | Low | Pages report is the primary deployment; the app is a bonus |
| Running out of time | — | Follow the cut list. Submit a working v0.9 by 12:00 and improve after |

## Definition of done (whole project)
- [ ] Public repo, MIT license, README with results filled in, CI green
- [ ] `pip install -r requirements.txt && make reproduce` works from a fresh clone
- [ ] Classical baseline + fair comparison table (doc 05)
- [ ] One-page business brief (`docs/BUSINESS_BRIEF.md` → PDF)
- [ ] 2-min demo video **or** 3 slides (do both if time allows)
- [ ] Hardware job ID + raw counts committed (bonus)
- [ ] `v1.0.0` release tagged before submission
