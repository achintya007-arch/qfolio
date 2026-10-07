"""Q-Folio: constraint-preserving QAOA for cardinality-constrained portfolio selection.

The pipeline is: prices → (μ, Σ) → ``PortfolioProblem`` → QUBO / Ising → QAOA circuit
→ samples → metrics, checked against classical baselines. See ``docs/02_ARCHITECTURE.md``.
"""

from qportfolio.problem import PortfolioProblem, bitstring_to_x, x_to_bitstring

__version__ = "1.0.0"  # keep in sync with pyproject.toml

__all__ = ["PortfolioProblem", "__version__", "bitstring_to_x", "x_to_bitstring"]
