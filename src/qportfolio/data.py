"""Load cached prices and turn them into annualised mean returns μ and covariance Σ.

No network access here: prices come from the committed ``data/prices.csv``
(only ``scripts/fetch_data.py`` downloads).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_prices(
    path: str | Path = "data/prices.csv",
    tickers: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """Load daily adjusted close prices (index = date, columns = tickers)."""
    raise NotImplementedError


def returns_stats(prices: pd.DataFrame, periods: int = 252) -> tuple[np.ndarray, np.ndarray]:
    """Annualised (μ, Σ) from daily log returns: μ = periods·mean(r), Σ = periods·cov(r)."""
    raise NotImplementedError


def synthetic_instance(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Random but realistic (μ, Σ) with Σ symmetric positive definite; offline fallback."""
    raise NotImplementedError
