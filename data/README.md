# Data card

| Field | Value |
|---|---|
| Source | Yahoo Finance via `yfinance` (public end-of-day prices) |
| Fetched by | `scripts/fetch_data.py` (the only network access in the project) |
| File | `prices.csv`: index = date, columns = tickers, values = adjusted close (INR) |
| Period | 2023-01-01 → 2025-12-31 (≈ 740 trading days) |
| Note | Recent `yfinance` returns adjusted prices in `Close` by default (`auto_adjust=True`). Record the yfinance version and fetch date in `prices.meta.json` |
| License / use | Non-commercial research and education; no redistribution beyond this reproducibility cache |
| Personal data | None |

## Universe (10 NSE large caps, chosen for sector diversity)
| Ticker | Company | Sector |
|---|---|---|
| RELIANCE.NS | Reliance Industries | Energy / conglomerate |
| TCS.NS | Tata Consultancy Services | IT services |
| HDFCBANK.NS | HDFC Bank | Banking |
| INFY.NS | Infosys | IT services |
| ITC.NS | ITC | FMCG |
| LT.NS | Larsen & Toubro | Infrastructure |
| SUNPHARMA.NS | Sun Pharmaceutical | Pharma |
| BHARTIARTL.NS | Bharti Airtel | Telecom |
| MARUTI.NS | Maruti Suzuki | Automobiles |
| HINDUNILVR.NS | Hindustan Unilever | FMCG |

- Headline instance (n = 6, k = 3): the first six.
- Hardware instance (n = 4, k = 2): RELIANCE, TCS, HDFCBANK, ITC.
- Robustness set: random 6-subsets of all ten (seeded).

**Fallback:** if a fetch fails, `data.synthetic_instance(n, seed)` produces a correlated synthetic market. The README must say clearly which data each result used.
