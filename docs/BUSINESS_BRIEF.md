# Q-Folio: one-page business brief
*Qiskit Fall Fest 2026 · Track I2 · Achintya Akella*

**Customer.** Indian wealth-tech and robo-advisory platforms that sell curated, equal-weight "model baskets" (themed portfolios of a few stocks) to retail investors. Each platform maintains hundreds of baskets across risk profiles and rebalances them periodically.

**The problem and its cost.** Choosing *which k stocks* go into a basket is a combinatorial optimisation. The number of candidate baskets grows as C(n,k): 20 options for 3-of-6, ~185 000 for 10-of-20, and astronomically more for real universes. Platforms rely on heuristics and analyst judgement, and a poorly chosen basket shows up directly as lower risk-adjusted return for clients. ⟨Add one sourced data point, e.g. size of India's robo-advisory/AUM market or number of demat accounts, with citation.⟩

**What we built.** A Qiskit pipeline that turns a basket-selection problem (expected returns, covariance, basket size k, client risk aversion q) into a quantum circuit. We use a **constraint-preserving QAOA**: the circuit only ever proposes baskets with exactly k stocks. It runs on simulators, on IBM noise models and on a real IBM quantum computer, and it is checked against exact and heuristic classical solvers.

**Result.** On ⟨6⟩ NSE large caps (k = ⟨3⟩, 2023–2025 prices):
- Constraint-preserving QAOA sampled the optimal basket with probability **⟨x⟩** vs **⟨0.05⟩** for random choice, and its most frequent answer **was** the optimum. Standard penalty-QAOA performed **at chance level (⟨y⟩)**.
- 100% of its samples were valid baskets (vs ⟨z⟩% for penalty-QAOA).
- On IBM hardware (`⟨backend⟩`, 4 assets), P(optimal) was **⟨h_raw⟩ raw → ⟨h_ps⟩ after symmetry post-selection** (random: 0.167).

**Limits (read this).**
- At this size a classical computer finds the exact answer instantly. **There is no quantum advantage today**, and we do not claim one.
- Today's hardware noise limits us to ~4–6 assets and shallow circuits.
- The model is simplified: equal weights, historical estimates, no costs or sector rules.

**Why it still matters / next steps.** The project shows that **encoding business constraints directly in the circuit** is necessary for quantum optimisation to work at all, and that it also gives built-in error detection. Next steps: sector and turnover constraints as further symmetries, parameter transfer across baskets, and benchmarking against commercial MIQP solvers as hardware matures.

**Links:** Repo ⟨url⟩ · Report ⟨url⟩ · Live demo ⟨url⟩ · Video ⟨url⟩

<sub>Public market data only. Not investment advice.</sub>
