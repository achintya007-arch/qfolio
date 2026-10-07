# ADR-0001: Implement QAOA directly on Qiskit V2 primitives

**Status:** Accepted · 2026-10-07

## Context
`qiskit-algorithms` and `qiskit-optimization` provide QAOA and `PortfolioOptimization` classes, but they are community-maintained, change their APIs separately from Qiskit core, and hide the circuit. The judging awards 25 points for "Qiskit implementation".

## Decision
Build the ansatz with `qiskit.circuit.library.QAOAAnsatz` (core), optimise with `StatevectorEstimator` + SciPy, and sample with any V2 sampler (statevector, Aer, IBM Runtime).

## Consequences
+ Full control (custom mixer, initial state, parameter order), fewer dependencies, a single code path from simulator to hardware.
+ The internals can be explained line by line in the demo.
− About 150 more lines of our own code, so more tests are needed (docs/08).
