"""Data sanity: the cached CSV loads offline and gives a valid (μ, Σ)."""

from pathlib import Path

import numpy as np
import pytest

from qportfolio.data import load_prices, returns_stats, synthetic_instance

CSV = Path(__file__).resolve().parents[1] / "data" / "prices.csv"
HEADLINE = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "LT.NS"]


def assert_valid_covariance(sigma: np.ndarray, n: int) -> None:
    assert sigma.shape == (n, n)
    np.testing.assert_allclose(sigma, sigma.T, atol=1e-14)
    assert np.linalg.eigvalsh(sigma).min() > 0  # PSD (strictly PD here)


def test_cached_csv_loads():
    prices = load_prices(CSV)
    assert prices.shape[1] == 10
    assert len(prices) > 700
    assert prices.index.is_monotonic_increasing
    assert not prices.isna().any().any()
    assert (prices > 0).all().all()


def test_load_prices_selects_tickers_and_dates():
    prices = load_prices(CSV, tickers=HEADLINE, start="2024-01-01", end="2024-12-31")
    assert list(prices.columns) == HEADLINE
    assert prices.index.min().year == 2024
    assert prices.index.max().year == 2024


def test_load_prices_unknown_ticker():
    with pytest.raises(KeyError):
        load_prices(CSV, tickers=["NOPE.NS"])


def test_returns_stats_shapes_and_psd():
    mu, sigma = returns_stats(load_prices(CSV, tickers=HEADLINE))
    assert mu.shape == (6,)
    assert_valid_covariance(sigma, 6)
    # Annualised vols of NSE large caps sit roughly in 10–60 %.
    vol = np.sqrt(np.diag(sigma))
    assert ((vol > 0.10) & (vol < 0.60)).all()


def test_returns_stats_formula():
    prices = load_prices(CSV, tickers=HEADLINE[:2])
    r = np.diff(np.log(prices.to_numpy()), axis=0)
    mu, sigma = returns_stats(prices, periods=252)
    np.testing.assert_allclose(mu, 252 * r.mean(axis=0))
    np.testing.assert_allclose(sigma, 252 * np.cov(r, rowvar=False))


def test_synthetic_instance_valid_and_seeded():
    mu, sigma = synthetic_instance(6, seed=7)
    assert mu.shape == (6,)
    assert_valid_covariance(sigma, 6)
    mu2, sigma2 = synthetic_instance(6, seed=7)
    np.testing.assert_array_equal(mu, mu2)
    np.testing.assert_array_equal(sigma, sigma2)
