# Weekly Report: Quant Research Onboarding

**Period:** 2026-07-16 to 2026-07-17

**Theme:** Return calculation, panel-data hygiene, and factor timing

## Completed Work

- Ran a baseline synthetic multi-factor script and interpreted annualized return,
  volatility, Sharpe ratio, maximum drawdown, and turnover.
- Practiced grouped monthly return calculations on a three-stock panel.
- Traced how one missing price affects both the current and following return.
- Constructed and interpreted a two-month momentum signal.
- Separated current information used for a factor from future returns used for
  evaluation.

## Key Learning

A runnable backtest is not evidence of a tradable edge. Correct security-level
grouping, chronological ordering, missing-data treatment, and signal timing must
be established before interpreting performance.

## Negative Finding

The original baseline output used synthetic data and therefore could not support
a market-alpha claim. The small practice panel also cannot support statistical
conclusions about momentum.

## Next Week

1. Implement cross-sectional factor ranks.
2. Calculate and interpret monthly Rank IC.
3. Compare single-factor diagnostics before relying on a composite score.
4. Record code output and a reproducible commit in the next daily report.
