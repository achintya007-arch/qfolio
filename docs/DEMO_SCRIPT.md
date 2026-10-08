# Demo script, slides and video

## A. Slide deck: title + 3 slides (`docs/slides.pptx` / `docs/slides.pdf`)
Built by `scripts/make_slides.py` (python-pptx, numbers read from `results/*.json`), exported to PDF with PowerPoint.

**Title slide:** *"Q-Folio: Constraint-Preserving QAOA for Portfolio Selection"*, then event, track, name and university, plus "Real results on IBM Quantum ibm_kingston". Speaker note = the one-sentence pitch from `09_RUBRIC_MAP.md`.

**Slide 1: The problem**
- Title: *"Picking the best 3 of 6 stocks, on a quantum computer"*
- Visual: the risk/return frontier figure with all C(6,3) = 20 baskets as dots and the optimal basket highlighted
- Subtitle: robo-advisor model baskets · NSE large caps · return ↑ risk ↓

**Slide 2: The idea and the result**
- Left: two circuit cartoons, "Penalty QAOA: searches 64 strings, 44 invalid" vs "XY-QAOA: Dicke state + XY mixer, only the 20 valid baskets"
- Right: `headline.png` (P(optimal) bars + random line)
- Callout: *"~7× chance (P(optimal) 0.34 vs 0.05, 24 instances) · 100% valid · penalty-QAOA = chance (0.04, 75% valid)"*

**Slide 3: Real hardware and honesty**
- Subtitle: *P(optimal) 0.51 raw → 0.65 post-selected vs 0.17 random · job db3b1bimb58s7387e0jg*
- `noise_ladder.png` (ideal → fake_torino noisy sim → ibm_kingston raw → post-selected → post-selected + readout-mitigated)
- `results/hardware/ibm_job_histogram.png` next to it, caption: *"Real ibm_kingston output — tallest bar 1001 = optimal basket (RELIANCE+ITC), second 1100 = runner-up"* (this is PUB 1, the p = 1 circuit)
- Three bullets: "symmetry post-selection = free error detection" · "classical brute force is still faster at this size" · "next: more constraints as circuit symmetries"
- Repo + report links as text (no QR codes; add them by hand if wanted)

## B. 2-minute video script (screen recording + voice; ~260 words)

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Slide 1 | "Robo-advisors sell model baskets: pick k stocks out of n so return goes up and risk goes down. The number of choices explodes combinatorially. I built this with Qiskit." |
| 0:15–0:40 | Notebook: QUBO cell + penalty results | "The textbook approach turns 'exactly k stocks' into a penalty. I tested that carefully, with three penalty strengths and also CVaR. It finds the best basket no more often than random guessing." |
| 0:40–1:05 | Circuit diagram (Dicke + XY mixer) | "So I moved the constraint into the circuit. A Dicke state starts in an equal mix of only valid baskets, and an XY mixer swaps stocks in and out without ever changing the count. Every shot is a valid portfolio." |
| 1:05–1:25 | `headline.png` + benchmark table | "Across 24 test instances the optimal basket comes up 34% of the time, about 7 times more often than random guessing at 5%. That is on par with simulated annealing at 36%, and its most frequent answer is the optimum on 75% of instances. On the real NSE basket the top two answers are only 1.4% apart, so there I look at the top two: 37% vs 10% for random." |
| 1:25–1:45 | IBM dashboard job page → `noise_ladder.png` | "On IBM's ibm_kingston, noise lets about 22% invalid baskets through. The ideal circuit can't produce them, so I discard them. That's free error detection: the optimal basket goes from 51% to 65%, against 17% for random, and the top answer is the true optimum." |
| 1:45–2:00 | Slide 3 | "Honest limits: at this size a laptop solves it instantly, so there's no quantum advantage claimed. But building constraints into the circuit is what makes quantum optimisation work at all. Code, report and live demo are linked." |

Record with OBS or the Windows/Mac screen recorder at 1080p. Upload to YouTube as **Unlisted**. Put the link in the README and the brief.

## C. 3-minute live demo (if you reach the top 3, Day 3 13:00)
1. (20 s) The pitch sentence from `09_RUBRIC_MAP.md`.
2. (60 s) Live app: choose 6 tickers, k = 3, q = 0.5 → run → brute force picks RELIANCE+ITC+LT. Show QAOA's distribution next to it. **Do not claim QAOA's top answer = brute force here:** in `results/benchmark.json` the p = 2 top answer on this instance is RELIANCE+HDFCBANK+LT (4th best; the best two are only 1.4% apart). Say "approximation ratio 0.84, top-2 probability 0.37 vs 0.10 random". Change q to 1.0 and brute force swaps RELIANCE (20.0% vol) for HDFCBANK (18.6% vol), giving HDFCBANK+ITC+LT. *The business story in one click.* Check both in the live app before the demo.
3. (40 s) "Why XY beats penalty" tab.
4. (40 s) Hardware tab: job `db3b1bimb58s7387e0jg` on ibm_kingston, noise ladder, 0.51 → 0.65 vs 0.17 random. Backup: the dashboard screenshots in `results/hardware/`.
5. (20 s) Limits + thank you.
Have the app **already open and warmed up** (cache filled), plus a backup: the Pages report and a local `streamlit run`.
