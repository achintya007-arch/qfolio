"""Print the headline instance: μ, Σ, every feasible basket sorted by cost, and the optimum.

Usage: python scripts/show_instance.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qportfolio.classical import brute_force
from qportfolio.config import load_config
from qportfolio.data import load_prices, returns_stats
from qportfolio.problem import PortfolioProblem, x_to_bitstring


def main() -> None:
    """Build the default problem from config and print it."""
    cfg = load_config().raw
    d, prob = cfg["data"], cfg["problem"]
    tickers = d["tickers"]
    prices = load_prices(d["path"], tickers, d["start"], d["end"])
    mu, sigma = returns_stats(prices)
    p = PortfolioProblem(mu, sigma, k=prob["k"], q=prob["q"], labels=tuple(tickers))

    names = [t.removesuffix(".NS") for t in tickers]
    print(f"Prices: {len(prices)} days, {prices.index[0].date()} → {prices.index[-1].date()}")
    print(f"n = {p.n}, k = {p.k}, q = {p.q}\n")
    print("μ (annualised mean log return) and σ (annualised volatility):")
    print(pd.DataFrame({"mu": mu, "vol": np.sqrt(np.diag(sigma))}, index=names).round(4))
    print("\nΣ (annualised covariance):")
    print(pd.DataFrame(sigma, index=names, columns=names).round(4))

    best, costs = brute_force(p)
    feas = p.feasible_set()
    order = np.argsort(costs)
    print(f"\nAll {len(feas)} feasible baskets, best first (C = q·xᵀΣx − μᵀx):")
    print(f"{'rank':>4}  {'bitstring':>9}  {'cost':>8}  {'μᵀx':>7}  {'xᵀΣx':>7}  basket")
    for rank, i in enumerate(order, start=1):
        x = feas[i]
        basket = ", ".join(n for n, b in zip(names, x, strict=True) if b)
        bits, ret, risk = x_to_bitstring(x), mu @ x, x @ sigma @ x
        print(f"{rank:>4}  {bits:>9}  {costs[i]:>8.4f}  {ret:>7.4f}  {risk:>7.4f}  {basket}")

    chosen = ", ".join(n for n, b in zip(names, best.x, strict=True) if b)
    print(f"\nOptimum: {chosen}  (bitstring {x_to_bitstring(best.x)}, Qiskit order)")
    print(f"  cost = {best.cost:.4f}, gap to 2nd best = {np.sort(costs)[1] - best.cost:.4f}")
    print(f"  random-guess P(optimal) = 1/{len(feas)} = {1 / len(feas):.3f}")


if __name__ == "__main__":
    main()
