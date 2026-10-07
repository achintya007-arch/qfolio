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
    """Load daily adjusted close prices (index = date, columns = tickers).

    Rows with a missing price in any selected column are dropped, so every asset is
    measured on the same trading days (needed for a valid covariance).
    """
    prices = pd.read_csv(path, index_col=0, parse_dates=True).sort_index()
    if tickers is not None:
        missing = set(tickers) - set(prices.columns)
        if missing:
            raise KeyError(f"tickers not in {path}: {sorted(missing)}")
        prices = prices[list(tickers)]
    prices = prices.loc[start:end]
    return prices.dropna()


def returns_stats(prices: pd.DataFrame, periods: int = 252) -> tuple[np.ndarray, np.ndarray]:
    """Annualised (μ, Σ) from daily log returns: μ = periods·mean(r), Σ = periods·cov(r)."""
    r = np.log(prices / prices.shift(1)).dropna()
    mu = periods * r.mean().to_numpy()
    sigma = periods * r.cov().to_numpy()
    return mu, sigma


def synthetic_instance(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Random but realistic (μ, Σ) with Σ symmetric positive definite; offline fallback.

    Uses a one-factor market model: every asset loads on a common "market" factor plus its own
    noise, which gives positive correlations (≈ 0.2–0.6) like real equities.
    """
    rng = np.random.default_rng(seed)
    mu = rng.uniform(0.05, 0.25, n)  # 5–25 % annual return
    beta = rng.uniform(0.5, 1.5, n)  # market loadings
    market_vol = 0.15
    idio_vol = rng.uniform(0.15, 0.30, n)
    sigma = market_vol**2 * np.outer(beta, beta) + np.diag(idio_vol**2)
    return mu, sigma
