# Resume Bullets

These bullets accurately describe the current synthetic-data implementation. They intentionally make no claim of historical-market alpha or live performance.

- Built a reproducible Python pipeline for 100-stock, 120-month synthetic equity research, engineering 12-to-1 momentum, book-to-market, ROE, and low-volatility factors with a three-month fundamental lag, monthly winsorization, and cross-sectional z-score normalization.

- Evaluated factor rankings with monthly Rank IC/ICIR and five-quantile return spreads, then constructed an equal-weight top-quintile portfolio against an eligible-universe benchmark with return-drift-aware one-way turnover and automated 0-50 bps transaction-cost sensitivity.

- Developed twelve pytest checks for deterministic generation, ticker-level return boundaries, momentum timing, composite eligibility, missing returns, monthly continuity, universe coverage, drift-aware turnover, annualization, and drawdown, and automated seven CSV files plus one PNG with explicit synthetic-data disclosures.

## Usage Notes

- Keep the word `synthetic` when describing the current dataset.
- Do not place the synthetic return, Sharpe ratio, drawdown, or IC values on a resume as market performance.
- Do not claim point-in-time historical fundamentals; the implemented three-month shift is a demo convention.
- Do not claim live trading, market impact, exposure neutralization, or out-of-sample historical validation.
- Keep employer code, data, parameters, and results separate from this independent project unless public disclosure is explicitly approved.

## Maintainer

[WenqiDing-CompFin](https://github.com/WenqiDing-CompFin)
