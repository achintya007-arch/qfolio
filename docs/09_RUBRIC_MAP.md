# 09 · Judging rubric → evidence

| Criterion | Pts | What earns full marks | Where it is in this repo |
|---|---|---|---|
| **Qiskit implementation** | 25 | Correct, non-trivial, idiomatic Qiskit 2.x; beyond the tutorial | Hand-built QAOA on V2 primitives; Bärtschi–Eidenbenz Dicke circuit; weight-conserving XY mixer (pitfall #1 found and fixed); transpiler study; Runtime SamplerV2 with DD + twirling. `src/qportfolio/circuits.py`, `qaoa.py`, `noise.py` |
| **Industry relevance** | 20 | Real customer, real cost, realistic data | Robo-advisor model baskets; NSE large caps; risk-aversion profiles mapped to q. `docs/BUSINESS_BRIEF.md`, frontier figure |
| **Classical benchmark** | 20 | Strong baselines, the same objective, honest timing | Brute force + SA + greedy on the identical objective; 20+ instances, mean ± std. `docs/05_BENCHMARK_PROTOCOL.md`, `results/benchmark.json` |
| **Presentation & brief** | 20 | Clear story, honest limits, a crisp brief | One-page brief, 3 slides, 2-min video, Pages report, live app. `docs/DEMO_SCRIPT.md` |
| **Code quality** | 15 | Readable, tested, reproducible, documented | Typed modules, pytest (AC1–AC8), ruff, CI matrix, `make reproduce`, ADRs, pinned requirements |
| **Bonus: real hardware** | +10 | A real run with evidence | `results/hardware/<job_id>.json` + dashboard screenshot + noise ladder |

## The one-sentence pitch (memorise it)
> "Standard QAOA treats 'pick exactly k stocks' as a penalty and ends up no better than a coin flip. We built the constraint into the circuit, so every shot is a valid portfolio. It finds the optimal basket about 7× more often than chance, and the same symmetry lets us throw out hardware errors for free on a real IBM device."

## Questions judges will likely ask, with answers
- **"Is this faster than classical?"** No. At 6 assets brute force takes microseconds. We show the method and its limits; see the scaling figure.
- **"Why equal weights?"** It keeps the decision binary (qubit = hold/don't hold) and matches model-basket products. Continuous weights would need more qubits per asset.
- **"Why did penalty-QAOA fail?"** The penalty dominates the energy scale. The optimiser spends its few parameters learning feasibility, and the real return/risk differences become tiny by comparison.
- **"Is post-selection cheating?"** No. The ideal circuit provably conserves Hamming weight (test AC4), so a wrong-weight shot can only come from an error. This is called symmetry verification. We report raw numbers next to it.
- **"How did you pick the parameters?"** Exact-expectation optimisation on a statevector simulator with 8 restarts, including a linear-ramp warm start, then reused unchanged on hardware.
- **"What would make this useful at scale?"** Lower-error hardware for deeper circuits, parameter transfer between instances, and evidence of better scaling than SA on hard instances. None of these exist yet.
