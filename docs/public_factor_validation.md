# Public Real-Data Validation

## Purpose

The stock-level research engine uses synthetic observations to validate timing,
portfolio accounting, and failure behavior. This companion analysis adds real
market evidence without pretending that freely available aggregate factor
returns solve the harder point-in-time security-data problem.

## Official Sources

- [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- `F-F_Research_Data_5_Factors_2x3_CSV.zip`
- `F-F_Momentum_Factor_CSV.zip`

The five-factor archive supplies market excess return, size (`SMB`), value
(`HML`), profitability (`RMW`), investment (`CMA`), and the risk-free rate. The
momentum archive supplies `Mom`. The loader converts percentage returns to
decimal monthly returns, aligns the two datasets by month, caches the original
archives outside Git, and records their SHA-256 hashes.

## Current Official Snapshot

As reported by the Data Library for May 2026:

| Factor | May 2026 | Last 3 months | Last 12 months |
|---|---:|---:|---:|
| Market excess | 4.90% | 9.42% | 25.63% |
| Size (`SMB`) | -2.77% | -1.89% | 6.14% |
| Value (`HML`) | -2.15% | 0.42% | 14.53% |
| Profitability (`RMW`) | -8.42% | -15.98% | -27.50% |
| Investment (`CMA`) | -1.39% | -5.28% | -2.92% |

The mixed signs are the useful finding: factor performance is regime-dependent,
and quality/profitability can be sharply negative even while the broad market
and value factors are positive. The table is a source snapshot, not a statistical
claim and not a result of this repository's stock-selection strategy.

## Reproduction

```bash
python run_public_factor_validation.py --start-date 1990-01-01
```

The generated analysis reports annualized mean and volatility, zero-risk-free-
rate Sharpe ratio, maximum drawdown, positive-month ratio, a six-lag Newey-West
t-statistic for the monthly mean, fixed subperiod summaries, factor correlations,
and a cumulative-return chart.

The fixed regimes are 1990-2006, 2007-2019, and 2020-latest. They are declared in
code rather than selected after inspecting favorable results.

## Methodology Boundary

The Data Library states that its U.S. research returns switched from CRSP's
legacy FIZ files to CIZ files beginning with the January 2025 release. Under CIZ,
monthly returns compound daily returns and reinvest dividends on ex-dates; this
differs from the earlier month-to-month legacy construction. Any long-history
comparison must retain that documented methodology break.

This real-data module closes only the "no real observations anywhere" presentation
gap. It does not close the stock-level open risks in `failure_analysis.md`:

- no point-in-time security fundamentals;
- no inactive-security and delisting panel;
- no sector/size-neutral stock-level test;
- no frozen stock-level out-of-sample strategy result;
- no executable security-level spread, impact, or capacity estimate.
