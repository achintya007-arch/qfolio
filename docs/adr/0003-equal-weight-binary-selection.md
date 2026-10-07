# ADR-0003: Equal-weight binary selection (no continuous weights)

**Status:** Accepted · 2026-10-07

## Context
Continuous or integer weights need several qubits per asset, which is beyond what noisy hardware can handle at a useful depth.

## Decision
One qubit per asset (hold / don't hold), with equal weights over exactly k selected assets.

## Consequences
+ n qubits for n assets; matches equal-weight model-basket products.
− Cannot express weight optimisation; this is listed in Limits.
