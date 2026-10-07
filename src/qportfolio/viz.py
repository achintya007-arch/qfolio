"""One matplotlib function per figure (docs/05_BENCHMARK_PROTOCOL.md §7).

Every figure is saved as PNG (dpi 200) and SVG via :func:`save_figure`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def save_figure(fig: Figure, name: str, outdir: str | Path = "results/figures") -> Path:
    """Save ``fig`` as ``<name>.png`` (dpi 200) and ``<name>.svg``; return the PNG path."""
    raise NotImplementedError


def headline(benchmark: dict[str, Any]) -> Figure:
    """P(optimal) by method, with a dashed line at random 1/C(n, k)."""
    raise NotImplementedError


def feasibility(benchmark: dict[str, Any]) -> Figure:
    """P(feasible) for penalty vs XY QAOA across reps p."""
    raise NotImplementedError


def distribution(benchmark: dict[str, Any]) -> Figure:
    """Sampled cost distribution of XY-QAOA vs uniform-random feasible, optimum marked."""
    raise NotImplementedError


def noise_ladder(noisy: dict[str, Any], hardware: dict[str, Any] | None = None) -> Figure:
    """Ideal → noisy raw → post-selected → mitigated → real hardware."""
    raise NotImplementedError


def transpile(noisy: dict[str, Any]) -> Figure:
    """Depth and 2-qubit gate count vs optimisation level, per backend."""
    raise NotImplementedError


def frontier(benchmark: dict[str, Any]) -> Figure:
    """Risk vs return of all C(n, k) baskets with the chosen basket highlighted."""
    raise NotImplementedError


def scaling() -> Figure:
    """C(n, k) and XY-QAOA 2-qubit gate count vs n (log scale); honest context."""
    raise NotImplementedError
