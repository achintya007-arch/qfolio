"""Download adjusted daily closes with yfinance → ``data/prices.csv`` (+ ``prices.meta.json``).

This is the ONLY script in the project that touches the network. Run it once and commit the CSV;
tests, CI and every other script read the cached file.

Usage: python scripts/fetch_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Fetch the configured universe and write the CSV and its metadata."""
    cfg = yaml.safe_load((ROOT / "configs/default.yaml").read_text(encoding="utf-8"))["data"]
    tickers = cfg["universe"]
    # yfinance's `end` is exclusive, so ask for one day past the configured end date.
    end = (date.fromisoformat(cfg["end"]) + timedelta(days=1)).isoformat()

    # auto_adjust=True: `Close` is already adjusted for splits and dividends.
    raw = yf.download(tickers, start=cfg["start"], end=end, auto_adjust=True, progress=False)
    if raw is None or raw.empty:
        print("yfinance returned no data (network / proxy?). prices.csv not written.")
        return 1

    prices = raw["Close"][tickers].sort_index()
    prices.index = prices.index.date
    prices.index.name = "Date"
    missing = [t for t in tickers if prices[t].isna().all()]
    if missing:
        print(f"no data for {missing}; prices.csv not written.")
        return 1

    out = ROOT / cfg["path"]
    prices.round(4).to_csv(out)
    meta = {
        "source": "Yahoo Finance via yfinance (auto_adjust=True, Close)",
        "yfinance_version": yf.__version__,
        "fetched": datetime.now(UTC).isoformat(timespec="seconds"),
        "start": cfg["start"],
        "end": cfg["end"],
        "tickers": tickers,
        "rows": len(prices),
        "first_date": str(prices.index[0]),
        "last_date": str(prices.index[-1]),
        "missing_values": {t: int(n) for t, n in prices.isna().sum().items() if n},
    }
    out.with_name("prices.meta.json").write_text(json.dumps(meta, indent=2) + "\n", "utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(prices)} rows x {len(tickers)} tickers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
