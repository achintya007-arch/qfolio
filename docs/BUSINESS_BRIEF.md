# Q-Folio: one-page business brief
*Qiskit Fall Fest 2026 · Track I2 · Akella Ahlad Achintya*

**Customer.** Indian wealth-tech and robo-advisory platforms that sell curated, equal-weight "model baskets" (themed portfolios of a few stocks) to retail investors. Each platform maintains hundreds of baskets across risk profiles and rebalances them periodically.

**The problem and its cost.** Choosing *which k stocks* go into a basket is a combinatorial optimisation. The number of candidate baskets grows as C(n,k): 20 options for 3-of-6, ~185 000 for 10-of-20, and astronomically more for real universes. Platforms rely on heuristics and analyst judgement, and a poorly chosen basket shows up directly as lower risk-adjusted return for clients. The market is large and still growing: India had **23.4 crore (234.4 million) demat accounts in July 2026**, up 1.25% in one month ([360 ONE Capital data via ANI](https://www.newkerala.com/news/a/demat-accounts-rise-125-mom-2344-million-july-756.htm)).

**What we built.** A Qiskit pipeline that turns a basket-selection problem (expected returns, covariance, basket size k, client risk aversion q) into a quantum circuit. We use a **constraint-preserving QAOA** (Dicke initial state + XY mixer): the circuit only ever proposes baskets with exactly k stocks. It runs on simulators, on IBM noise models and on a real IBM quantum computer, and it is checked against exact and heuristic classical solvers.

**Result** (3-of-6 baskets, 2023–2025 NSE prices, p = 2, 8192 shots):

- **Validity.** 100% of XY-QAOA samples were valid baskets. Standard penalty-QAOA produced only 75% valid baskets and found the optimum at **chance level** (P(optimal) 0.04 vs 0.05 random).
- **Robustness, 24 instances.** XY-QAOA sampled the optimal basket with P = **0.34 ± 0.16** vs **0.05** for a random valid basket, comparable to simulated annealing on the same objective (0.36 ± 0.08). Its most frequent answer was the optimum on 75% of instances.
- **The real NSE basket (6 large caps).** The best and second-best baskets differ by only 1.4% of the cost range, so we report P(top-2) and approximation ratio here: XY-QAOA P(top-2) **0.37** vs 0.10 random, approximation ratio **0.84** vs 0.52 random.
- **Real IBM hardware** (`ibm_kingston`, 4 stocks, k = 2, job `db3b1bimb58s7387e0jg`): P(optimal) **0.51 raw → 0.65 after symmetry post-selection** vs 0.17 random, and the top answer was the true optimum.

**Limits (read this).**

- At this size a classical computer finds the exact answer in under a millisecond (brute force, greedy). **There is no quantum advantage today**, and we do not claim one.
- Today's hardware noise limits us to ~4–6 assets and shallow circuits (22% of raw hardware shots were invalid baskets).
- The model is simplified: equal weights, historical estimates, no costs or sector rules.

**Why it still matters / next steps.** The project shows that **encoding business constraints directly in the circuit** is necessary for quantum optimisation to work at all, and that it also gives built-in error detection. Next steps: sector and turnover constraints as further symmetries, parameter transfer across baskets, and benchmarking against commercial MIQP solvers as hardware matures.

**Links:** [Repo](https://github.com/achintya007-arch/qfolio) · [Report](https://achintya007-arch.github.io/qfolio/) · [Live demo](https://qfolio.streamlit.app)

<sub>Public market data only. Not investment advice. All numbers from `results/benchmark.json` and `results/hardware/db3b1bimb58s7387e0jg.json`.</sub>
