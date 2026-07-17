# Failure Analysis and Research Risk Register

**Author:** WenqiDing-CompFin

**Scope:** Monthly four-factor research pipeline

**Status date:** Current repository implementation

## 1. Purpose

A credible quantitative project records defects, weak results, invalid claims, and unresolved risks instead of presenting only an attractive equity curve. This document distinguishes:

- historical implementation defects that were found and fixed;
- current safeguards that prevent silent errors;
- weak or null synthetic diagnostics that must remain visible;
- open research limitations that block real-market conclusions.

No real-market factor hypothesis has passed or failed yet. The repository currently contains a synthetic-data demonstration, not a point-in-time empirical equity study.

## 2. Historical Defects: Found and Fixed

The following defects applied to an earlier prototype. They are **not current open defects**.

| ID | Historical defect | Risk created | Final implementation | Verification | Status |
|---|---|---|---|---|---|
| FIX-01 | Momentum applied a global shift after a grouped price change. | A prior ticker's final value could cross into the next ticker. | Momentum now uses `grouped_close.shift(1) / grouped_close.shift(12) - 1`. | `test_momentum_uses_only_prior_prices`; direct within-ticker implementation. | Fixed |
| FIX-02 | Composite score used a row mean that skipped missing factors. | Stocks could be compared using different subsets of factors, including during warm-up. | The z-score sum uses `min_count=4` and divides by four. | Source inspection and complete-score eligibility in the backtest. | Fixed |
| FIX-03 | Next-period prices were selected with a future-date `groupby.first` operation. | Missing intermediate observations could be skipped, producing variable holding periods and silent survivor effects. | `future_return_1m` is a direct within-ticker one-period shift; eligible missing future returns raise an error. | `test_future_return_does_not_cross_tickers`; explicit hard-failure branch. | Fixed |
| FIX-04 | Turnover used a set symmetric-difference count with an unclear scale. | Costs could be over- or under-charged and portfolio-weight drift was ignored. | Prior holdings are drifted by realized returns, then one-way turnover is `0.5 * sum(abs(target_weight - pretrade_weight))`; initial investment is charged as 1.0. | `test_first_turnover_is_full_investment` and `test_turnover_accounts_for_weight_drift`. | Fixed |
| FIX-05 | Drawdown could ignore a loss in the first return observation. | Maximum drawdown could be understated when the series began below initial capital. | Wealth is compared with a running peak clipped at the initial wealth level of 1.0. | `test_drawdown_includes_a_negative_first_month`. | Fixed |
| FIX-06 | Positive IC ratio treated warm-up NaNs as non-positive months. | The reported positive-month fraction was biased downward. | Each factor now drops missing IC values before computing the fraction above zero. | Corrected summary output and valid-observation counts. | Fixed |
| FIX-07 | A within-ticker row shift did not prove that adjacent rows were adjacent calendar months. | A missing row could turn a two-month move into a mislabeled one-month return. | Input validation now requires consecutive calendar months within each ticker. | `test_monthly_gap_is_rejected`. | Fixed |
| FIX-08 | Trailing volatility included the return ending at the signal-date close while the holding return began from that close. | The signal assumed knowledge at the same price used for entry. | The 12-month rolling standard deviation is shifted one additional month within ticker. | Direct lagged implementation and composite warm-up test. | Fixed |
| FIX-09 | The backtest silently skipped an undersized eligible universe after portfolio formation began. | A holding month, weight drift, and cost could disappear while annualization still treated observations as consecutive. | Warm-up months may wait for coverage, but any post-start month below `min_stocks` now raises an error. | `test_low_eligibility_after_start_is_not_silently_skipped`. | Fixed |

These fixes should remain in the regression suite. A future refactor that breaks one of them reopens the corresponding issue.

## 3. Current Safeguards

The final implementation currently provides:

- unique `(date, ticker)` validation;
- positive observed-price validation;
- consecutive-month validation within ticker;
- deterministic synthetic generation for a fixed seed;
- within-ticker factor lags and future returns;
- low-volatility data ending at `t-1` or earlier;
- a complete-case four-factor composite;
- a hard error when an eligible stock lacks a next-month return;
- an equal-weight eligible-universe benchmark;
- one-way turnover and explicit cost deduction;
- cost scenarios at 0, 5, 10, 20, and 50 bps;
- Rank IC and IC summary outputs;
- positive IC ratios based only on valid IC observations;
- five-quantile return and top-minus-bottom outputs;
- initial-wealth-aware maximum drawdown;
- twelve passing regression tests.

These safeguards improve correctness. They do not solve real-data provenance, survivorship, point-in-time, or deployment problems.

## 4. Invalid Claims

### Claim A: "The synthetic Sharpe ratio proves market alpha."

**Verdict:** Invalid.

Synthetic returns are explicitly generated with latent value and quality terms and a previous-return term. `book_to_market` and `roe` are noisy transformations of the same latent variables. The experiment is partly designed to contain relationships that the pipeline seeks to recover.

### Claim B: "The three-month accounting lag is point-in-time."

**Verdict:** Invalid.

A mechanical lag is only a demonstration convention. Real filings have security-specific publication dates, reporting delays, amendments, and restatements. Only an availability-timestamp join can support a point-in-time claim.

### Claim C: "The eligible-universe benchmark proves risk-adjusted alpha."

**Verdict:** Invalid.

The implemented benchmark is a useful equal-weight control. It is not an external investable index and does not control sector, size, beta, liquidity, leverage, or other common exposures.

### Claim D: "A 10 bps cost case is a live execution estimate."

**Verdict:** Invalid.

The cost sensitivity demonstrates portfolio accounting under flat assumptions. It does not estimate bid-ask spread, impact, tax, delay, market state, order size, borrow, or capacity.

### Claim E: "Rejecting missing next-month returns removes delisting bias."

**Verdict:** Invalid.

The hard error prevents silent omission. It does not supply the correct delisting return or historical security record. Those data must still be obtained and validated.

## 5. Open Risk Register

| ID | Severity | Open limitation | Why it matters | Required closure evidence | Status |
|---|---|---|---|---|---|
| OPEN-01 | Critical | Synthetic-only evidence | Engineered data cannot establish a real market relationship. | Reproduce the study on an audited real monthly panel. | Open |
| OPEN-02 | Critical | No actual fundamental publication dates | Mechanical three-month lags can still use unavailable or revised information. | Point-in-time joins based on original public availability timestamps. | Open |
| OPEN-03 | Critical | No real inactive/delisted security dataset | A current-survivor panel can overstate returns and understate loss. | Historical universe plus validated delisting returns and identifier mapping. | Open |
| OPEN-04 | Critical | No chronological untouched test | Reusing all observations for research encourages overfit conclusions. | Frozen specification evaluated once on a held-out final period. | Open |
| OPEN-05 | High | No sector or size neutralization | Composite returns may be industry or capitalization bets. | Raw and neutralized factor diagnostics with exposure reports. | Open |
| OPEN-06 | High | No beta or common-risk attribution | Lower risk or market exposure can be mistaken for alpha. | Benchmark-relative regression and exposure-matched comparisons. | Open |
| OPEN-07 | High | No historical investability rules | Tiny, illiquid, suspended, or invalid share classes can inflate paper returns. | Point-in-time price, size, liquidity, exchange, share-class, and suspension filters. | Open |
| OPEN-08 | High | Corporate-action policy absent for real data | Splits, dividends, mergers, and distributions can create false returns. | Documented total-return construction reconciled against an independent source. | Open |
| OPEN-09 | High | Flat transaction-cost model | Sensitivity is implemented, but cost realism is not. | Spread, impact, delay, tax, and capacity estimates by liquidity bucket. | Open |
| OPEN-10 | Medium | Benchmark analysis is basic | Monthly benchmark and excess returns exist, but no tracking error, information ratio, or beta summary is exported. | Reproducible benchmark-relative metric and attribution report. | Open |
| OPEN-11 | Medium | Quantile implementation analysis is incomplete | Quantile returns and top-minus-bottom spreads exist, but quantile turnover, costs, and uncertainty are not reported. | Add quantile portfolio turnover, costs, confidence intervals, and subperiod diagnostics. | Open |
| OPEN-12 | High | No dependence-robust inference | Mean IC can look stable while uncertainty is understated. | Confidence intervals and serial-dependence-aware inference where appropriate. | Open |
| OPEN-13 | High | Multiple-testing history absent | Trying many variants can generate a winner by chance. | Experiment registry, frozen baseline, and multiple-comparison control. | Open |
| OPEN-14 | Medium | Exact environment is not locked | Version ranges can resolve to different dependency versions later. | Exact lock file and clean-environment reproduction record. | Open |
| OPEN-15 | High | Capacity and operations untested | A statistically positive signal may not be executable at useful scale. | Capacity model, execution-delay stress, and paper-trading operations log. | Open |
| OPEN-16 | Medium | Real-data legal provenance unspecified | A public repository cannot redistribute data without permission. | Data license review and a documented acquisition procedure. | Open |

## 6. Weak and Null Synthetic Findings Kept Visible

The default synthetic output is not uniformly favorable:

| Factor | Mean Rank IC | Positive IC ratio | Interpretation limited to synthetic data |
|---|---:|---:|---|
| Momentum | 0.0016 | 49.5% | Essentially null at the implemented 12-1 horizon. |
| Value | 0.0248 | 56.9% | Positive, consistent with value being embedded in the generator. |
| Quality | 0.0427 | 62.1% | Strongest of the four, consistent with quality being embedded in the generator. |
| Low volatility | 0.0111 | 51.9% | Small average IC and only a slight majority of positive valid months. |

These observations should not be edited out because momentum and low volatility look weaker. They demonstrate the expected research practice: report all pre-specified factors, including null or inconvenient results.

They also do not justify rejecting momentum or low volatility in real markets. A synthetic null result tests this generator and specification, not the historical market hypothesis.

## 7. Signal-Specific Failure Modes

### 7.1 Momentum

Possible real-data failures:

- incorrect split or dividend adjustments;
- signal/execution timing overlap;
- high turnover and momentum crashes;
- concentration in small or illiquid stocks;
- sensitivity to one exact lookback window;
- reversal rather than persistence in the selected market.

Required tests:

- hand-calculated ticker fixtures and extreme-return audits;
- pre-specified 6-1, 9-1, and 12-1 comparisons;
- quantile returns, turnover, and conservative cost cases;
- crash-period, size, liquidity, and sector breakdowns;
- untouched-period Rank IC and spread.

### 7.2 Value

Possible real-data failures:

- stale, revised, or unavailable book equity;
- negative or very small denominators;
- a disguised sector, size, or distress exposure;
- mismatched market equity and accounting dates;
- dependence on one value-recovery episode.

Required tests:

- actual filing timestamps and original-vintage policy;
- explicit negative-book-equity treatment;
- sector- and size-neutral variants;
- leverage, distress, and liquidity controls;
- alternative valuation definitions where data permit.

### 7.3 Quality

Possible real-data failures:

- high ROE created by leverage, buybacks, or a small equity denominator;
- one-off income or accounting revisions;
- non-comparable sector accounting;
- overlap with low volatility, growth, or sector exposures;
- weak incremental information after value controls.

Required tests:

- point-in-time ROE components and denominator screens;
- leverage and sector controls;
- operating or gross-profitability alternatives;
- factor-correlation and incremental-IC analysis;
- subperiod stability.

### 7.4 Low Volatility

Possible real-data failures:

- the result is only low beta, not selection alpha;
- defensive-sector concentration;
- unstable estimates from monthly observations;
- slow response to abrupt risk changes;
- expensive low-risk stocks underperform in risk-on regimes.

Required tests:

- daily and monthly volatility comparisons;
- beta and residual-volatility variants;
- sector-neutral and beta-matched portfolios;
- 6-, 12-, and 24-month windows;
- regime, valuation, concentration, and liquidity analysis.

## 8. Failure Experiment Template

Every unsuccessful or ambiguous future test should remain in the research history:

```text
Experiment ID:
Date:
Code commit:
Hypothesis:
Pre-specified decision rule:
Data vintage and period:
Universe and timing rules:
Only parameter changed:
Expected result:
Observed result:
Gross and net result:
Benchmark result:
Diagnostics performed:
Likely explanation:
Decision: reject / revise / retain as control
Follow-up test, if justified:
```

An unfavorable IC, spread, Sharpe ratio, or holdout result is a legitimate research outcome. Deleting it creates selection bias.

## 9. Prioritized Remediation Gates

### Gate 1: Real-Data Integrity

1. Define stable identifiers and the historical investable universe.
2. Reconcile adjusted returns and corporate actions.
3. Include inactive securities and delisting returns.
4. Join fundamentals by actual release timestamp.

No real-market performance should be interpreted before Gate 1 passes.

### Gate 2: Research Design

1. Freeze factor definitions, exclusions, and timing.
2. Establish research, validation, and untouched test periods.
3. Register every parameter variant.
4. Add quantile and uncertainty diagnostics.

No robust-factor claim should be made before Gate 2 passes.

### Gate 3: Exposure and Benchmark Control

1. Add sector, size, beta, leverage, and liquidity attribution.
2. Compare raw, neutralized, and exposure-matched variants.
3. Export benchmark-relative risk and performance metrics.

No alpha claim should be made before Gate 3 passes.

### Gate 4: Implementation Realism

1. Estimate spread, impact, delay, tax, and capacity.
2. Stress turnover and market-state assumptions.
3. Complete a paper-trading period with an operational log.

No deployment claim should be made before Gate 4 passes.

## 10. Closure Rules

An open item moves to `Closed` only when:

- a code, data, or research change directly addresses it;
- an automated test or independently produced diagnostic verifies the change;
- the evidence is linked to a code version and immutable output;
- all affected results are regenerated;
- the report states whether the conclusion changed.

An unavoidable issue may be marked `Accepted limitation` only when its likely direction and magnitude are discussed and all claims are narrowed accordingly.

## 11. Current Bottom Line

The final implementation is materially more reliable than the initial prototype. The cross-ticker shift, partial-factor mean, `groupby.first` holding-period behavior, drift-aware turnover accounting, initial drawdown, IC denominator, monthly-gap, intermediate missing-return, low-eligibility skip, and low-volatility timing defects have been found and fixed. Rank IC, factor quantiles, the eligible-universe benchmark, and cost sensitivity are now implemented, with twelve passing tests protecting the principal boundaries.

The remaining blockers are research-data and validation problems, not hidden fixes to the reported synthetic numbers. Until actual publication dates, delistings, real data, a frozen out-of-sample test, neutralization, and realistic implementation analysis are added, the correct conclusion is:

> This repository is a reproducible synthetic-data research pipeline, not a validated trading strategy.
