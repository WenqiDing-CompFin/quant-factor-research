# Resume Bullets

These bullets accurately distinguish the synthetic stock-level implementation
from the official public factor-return validation. They intentionally make no
claim of stock-selection alpha or live performance.

**Primary application link:**
`https://github.com/WenqiDing-CompFin/quant-factor-research`. Do not add separate
lab or AAAI repository links to the same application entry; describe the lab as
an interactive demo available from the flagship repository.

- Built a reproducible Python pipeline for 100-stock, 120-month synthetic equity research, engineering 12-to-1 momentum, book-to-market, ROE, and low-volatility factors with a three-month fundamental lag, monthly winsorization, and cross-sectional z-score normalization.

- Evaluated factor rankings with monthly Rank IC/ICIR and five-quantile return spreads, then constructed an equal-weight top-quintile portfolio against an eligible-universe benchmark with return-drift-aware one-way turnover and automated 0-50 bps transaction-cost sensitivity.

- Developed fourteen pytest checks for deterministic generation, ticker-level return boundaries, momentum timing, composite eligibility, missing returns, monthly continuity, universe coverage, drift-aware turnover, annualization, drawdown, and public-data parsing and inference.
- Added a source-audited real-data module for official Fama-French five-factor and momentum portfolio returns, recording archive hashes and reporting fixed subperiods with Newey-West mean t-statistics while keeping aggregate factor evidence separate from the synthetic stock strategy.

## Usage Notes

- Keep the word `synthetic` when describing the current dataset.
- Do not place the synthetic return, Sharpe ratio, drawdown, or IC values on a resume as market performance.
- Do not claim point-in-time historical fundamentals; the implemented three-month shift is a demo convention.
- Do not claim live trading, market impact, exposure neutralization, or out-of-sample historical validation.
- Keep employer code, data, parameters, and results separate from this independent project unless public disclosure is explicitly approved.

## Maintainer

[WenqiDing-CompFin](https://github.com/WenqiDing-CompFin)
