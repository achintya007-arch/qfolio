# ADR-0002: Enforce the cardinality constraint with an XY mixer + Dicke state

**Status:** Accepted · 2026-10-07

## Context
Pre-build validation (docs/04) showed that penalty-QAOA reaches only random-level P(optimal) (0.03–0.05 vs 0.05) across λ ∈ {0.5, 1, 2}×range and with a CVaR objective.

## Decision
The primary method is XY-ring-mixer QAOA initialised in |D^n_k⟩ (Hadfield et al. 2019). Penalty-QAOA is kept as an explicit comparison.

## Consequences
+ 100% feasible samples; P(optimal) about 7× random at p=2; the top sample is the optimum.
+ Weight conservation lets us use symmetry post-selection on hardware.
− The Dicke preparation adds 2-qubit gates (24 at n=4, 73 at n=6), so hardware uses n=4.
− The mixer must be a gate-level circuit (pitfall #1).
