# Multi-Factor Equity Research Report

**Author:** WenqiDing-CompFin

**Project stage:** Reproducible synthetic stock-level pipeline plus separate public factor-return validation

The companion [`public_factor_validation.md`](public_factor_validation.md)
documents the official Kenneth French five-factor and momentum return path. It
adds real aggregate factor evidence while leaving every stock-selection claim in
this report subject to the synthetic-data boundary below.

**Research status:** Engineering validation only; no real-market alpha claim

**Signals:** Momentum, value, quality, and low volatility

**Frequency:** Monthly

## Executive Summary

This project implements a transparent monthly equity-factor research workflow. It validates an input panel, constructs four point-in-time-style signals, computes monthly Rank IC, forms an equal-weighted long-only portfolio from the highest composite scores, compares that portfolio with the equal-weighted eligible universe, applies turnover-based transaction costs, and exports reproducible diagnostics.

The default run uses deterministic synthetic data. The synthetic generator deliberately links returns to latent value and quality characteristics and includes short-horizon return persistence. Its output is useful for testing whether the research pipeline behaves as designed. It is **not** evidence that these factors earn alpha in a real market, and the reported return, Sharpe ratio, drawdown, IC, and cost sensitivity must not be presented as expected investment performance.

The implementation now addresses important timing and accounting defects found in the earlier prototype: ticker boundaries are respected, monthly gaps are rejected, low-volatility inputs are lagged, the composite requires all four factors, next-period returns are calculated directly rather than selected with `groupby.first`, turnover uses a one-way weight-change definition, drawdown includes losses from the initial wealth level, and positive IC ratios use only valid IC observations. These behaviors are supported by automated tests and explicit source checks.

The next valid stock-level research milestone is a study using licensed or public
security data with actual publication timestamps, inactive and delisted
securities, an untouched out-of-sample period, investability filters, and sector
and size controls.

## 1. Research Question

The primary research question is:

> After realistic timing, universe, risk, and cost controls, does an equal-weighted combination of momentum, value, quality, and low-volatility signals provide stable out-of-sample information about next-month cross-sectional equity returns?

The current synthetic experiment cannot answer that market question. It answers a narrower engineering question:

> Can the repository produce deterministic factors, diagnostics, portfolio returns, benchmark returns, cost scenarios, and saved artifacts without known cross-security or missing-factor errors?

## 2. Hypotheses

| Factor | Economic hypothesis | Direction | Main real-data falsification condition |
|---|---|---:|---|
| Momentum | Information may diffuse gradually, allowing intermediate-horizon relative strength to persist. | Higher is better | Rank IC and quantile spread are unstable or non-positive out of sample, or disappear after costs. |
| Value | Investors may overpay for popular firms or require compensation for holding inexpensive or distressed firms. | Higher book-to-market is better | Results are explained by stale accounting data, sector, size, distress, or a small number of episodes. |
| Quality | Profitable firms may compound capital more reliably, while the market may underweight persistent profitability. | Higher ROE is better | Results disappear after leverage and sector controls or rely on revised financial statements. |
| Low volatility | Leverage constraints and demand for lottery-like stocks may lead investors to overpay for high-risk securities. | Lower trailing volatility is better | Performance is entirely explained by beta, defensive sectors, valuation, or one market regime. |

These hypotheses are probabilistic. A high score does not imply that an individual stock must outperform next month.

## 3. Repository Workflow

The executable workflow is:

```text
CSV or deterministic synthetic panel
    -> schema and uniqueness validation
    -> within-ticker returns and lagged factors
    -> cross-sectional winsorization and z-scores
    -> monthly Rank IC and factor-quantile returns
    -> complete-case four-factor composite
    -> top-20% equal-weight portfolio
    -> equal-weight eligible-universe benchmark
    -> one-way turnover and cost deduction
    -> metrics, cost sensitivity, CSV outputs, and equity-curve chart
```

Main components:

| Component | Responsibility |
|---|---|
| `src/quant_factor/data.py` | Synthetic panel generation, CSV loading, and input validation. |
| `src/quant_factor/factors.py` | Factor construction, cross-sectional transformation, composite score, Rank IC, and quantile returns. |
| `src/quant_factor/backtest.py` | Portfolio selection, benchmark, one-way turnover, and transaction costs. |
| `src/quant_factor/metrics.py` | Annualized return, volatility, zero-risk-free-rate Sharpe ratio, drawdown, and positive-month ratio. |
| `run_research.py` | End-to-end orchestration, cost sensitivity, exports, and chart generation. |
| `tests/test_research.py` | Regression tests for deterministic data, timing boundaries, turnover, and drawdown. |

## 4. Data Contract

The input is a long-form monthly panel with one row per date and ticker.

| Column | Prototype meaning | Real-data requirement |
|---|---|---|
| `date` | Month-end observation and signal date | Must map to an actual trading calendar and decision timestamp. |
| `ticker` | Security identifier | Must be replaced or supplemented by a stable identifier that survives ticker changes and mergers. |
| `close` | Positive monthly closing price | Must use a documented split/dividend adjustment and a feasible execution convention. |
| `book_to_market` | Value characteristic | Book equity and market equity definitions, dates, revisions, and invalid denominators must be documented. |
| `roe` | Quality characteristic | Numerator, denominator, reporting period, announcement date, and revision policy must be documented. |

Validation currently rejects:

- missing required columns;
- an empty input panel;
- duplicate `(date, ticker)` rows;
- missing dates or tickers;
- non-positive observed prices.
- non-consecutive monthly observations within a ticker.

The monthly-continuity rule prevents a one-row shift from silently turning a two-month price move into a one-month target. It does not supply a missing observation or delisting return; real-data preparation must do that explicitly.

Real-data research also requires historical security status, delisting returns, exchange and share-class fields, market capitalization, free float, sector, liquidity, corporate actions, and actual fundamental publication timestamps. Those fields are not part of the current minimum contract.

## 5. Synthetic Data Design

The default experiment creates 100 securities over 120 month ends beginning in January 2015, using seed 7 unless another seed is supplied. The generator is deterministic for a fixed seed.

Its monthly return process includes:

```text
0.004
+ 0.0025 * latent_value
+ 0.0030 * latent_quality
+ 0.10 * previous_month_return
+ security-specific random noise
```

The generated `book_to_market` and `roe` fields are noisy transformations of the same latent value and quality variables. Positive value or quality diagnostics are therefore partly built into the experiment. The synthetic dates are labels for simulated periods, not historical observations from 2015-2024.

This design is appropriate for:

- deterministic unit and integration testing;
- detecting broken signal direction or timing;
- validating output schemas;
- demonstrating the research workflow.

It is not appropriate for:

- estimating real expected returns;
- claiming market alpha;
- choosing production parameters;
- estimating capacity or live costs;
- supporting an investment recommendation.

## 6. Factor Definitions and Timing

### 6.1 Momentum

At signal month `t`:

```text
momentum(i,t) = close(i,t-1) / close(i,t-12) - 1
```

The latest month is skipped. Both lags are computed inside each ticker, preventing observations from crossing security boundaries.

### 6.2 Value

The prototype uses:

```text
value(i,t) = book_to_market(i,t-3)
```

The three-month shift is a **mechanical demonstration lag**. It is not point-in-time accounting. A real study must use the date on which each filing or field became public, including restatement and revision policy.

### 6.3 Quality

The prototype uses:

```text
quality(i,t) = roe(i,t-3)
```

The same warning applies: a three-month lag cannot replace actual publication timestamps. Real-data tests must also examine leverage, negative or small book equity, one-off earnings, and sector comparability.

### 6.4 Low Volatility

The signal is the negative sample standard deviation of 12 monthly returns ending one month before the signal date:

```text
realized_volatility_12m(i,t) = std(return_1m from t-12 through t-1, ddof=1)
low_volatility(i,t) = -realized_volatility_12m(i,t)
```

The negative sign makes lower historical volatility rank higher. The extra one-period lag means the signal does not use the same month-end close from which the next holding-period return begins.

### 6.5 Prediction Target

The target used only for evaluation is:

```text
future_return_1m(i,t) = close(i,t+1) / close(i,t) - 1
```

It is computed within ticker. It is never included in factor construction.

## 7. Cross-Sectional Processing

Each factor is processed independently at every date:

1. Drop missing values for percentile estimation.
2. Require at least three valid cross-sectional observations.
3. Clip values at the 1st and 99th percentiles.
4. Subtract the clipped cross-sectional mean.
5. Divide by the clipped population standard deviation (`ddof=0`).

If a cross section is too small or has zero dispersion, its z-score is missing.

The composite is:

```text
composite_score = (momentum_z + value_z + quality_z + low_volatility_z) / 4
```

The implementation uses `min_count=4`; therefore, all four standardized factors must be present. It does not silently average a partial set of signals.

Equal weights are a transparent baseline. No factor-weight optimization is performed.

## 8. Factor Diagnostics

For each month and factor, the pipeline calculates Spearman Rank IC between the raw factor value at `t` and `future_return_1m` over `t` to `t+1`. At least three paired observations are required.

The exported summary contains:

- mean monthly Rank IC;
- standard deviation of monthly Rank IC;
- fraction of valid months with positive IC;
- number of valid monthly observations;
- `ICIR = mean Rank IC / Rank IC standard deviation`.

The ICIR is not annualized in the current output.

The pipeline also sorts each raw factor into five cross-sectional quantiles each month, reports equal-weight next-month returns for `q1` through `q5`, and calculates `q5 - q1`. This provides a direct check of direction and approximate monotonicity. It does not yet include quantile-specific turnover, costs, or statistical confidence intervals.

## 9. Portfolio and Benchmark Method

At each date, the backtest:

1. keeps securities with a complete composite score;
2. requires at least 20 eligible securities;
3. refuses to continue if any eligible security lacks its next-month return;
4. selects the highest-scoring 20% of the eligible universe;
5. assigns equal weights to selected securities;
6. records the equal-weighted return of all eligible securities as the benchmark;
7. records net excess return as portfolio net return minus benchmark return.

The benchmark is a useful internal control but is not a real market index. It inherits the same eligibility rules and synthetic-data limitations as the portfolio.

One-way turnover is defined as:

```text
turnover(t) = 0.5 * sum_i(abs(target_weight(i,t) - pretrade_weight(i,t)))
```

Prior target weights are first drifted by realized holding-period returns to form pretrade weights. The initial move from no holdings to full investment is charged at turnover 1.0. Trading cost is:

```text
trading_cost(t) = turnover(t) * cost_bps / 10,000
net_return(t) = gross_return(t) - trading_cost(t)
```

## 10. Performance Metrics

For monthly net returns, the pipeline reports:

```text
annual_return      = ending_wealth^(12 / months) - 1
annual_volatility  = monthly_std * sqrt(12)
sharpe_zero_rf     = monthly_mean / monthly_std * sqrt(12)
max_drawdown       = minimum(wealth / prior_peak_or_initial_wealth - 1)
positive_month_ratio = fraction of net months above zero
```

The Sharpe ratio assumes a zero risk-free rate. This is a naming and interpretation constraint, not a general Sharpe estimate for a real investment period.

## 11. Current Synthetic Results

All numbers in this section are pipeline-demonstration outputs generated from the default synthetic panel. They are not real-market findings.

### 11.1 Rank IC Summary

| Factor | Mean Rank IC | Rank IC std. | Positive IC ratio | Valid months | ICIR |
|---|---:|---:|---:|---:|---:|
| Momentum | 0.0016 | 0.1092 | 49.5% | 107 | 0.0149 |
| Value | 0.0248 | 0.0938 | 56.9% | 116 | 0.2647 |
| Quality | 0.0427 | 0.1116 | 62.1% | 116 | 0.3827 |
| Low volatility | 0.0111 | 0.1073 | 51.9% | 106 | 0.1033 |

The positive IC ratio uses only non-missing IC observations; warm-up months do not count as negative observations. The stronger synthetic quality and value results are consistent with the generator embedding those characteristics in returns. Momentum is close to zero at this specific 12-1 horizon despite the generator's one-month persistence term. This is a useful reminder that implementing a factor does not guarantee a favorable diagnostic, even in synthetic data.

### 11.2 Mean Factor-Quantile Returns

Each entry is the arithmetic mean next-month return for the indicated synthetic factor bucket.

| Factor | Q1 | Q2 | Q3 | Q4 | Q5 | Q5 - Q1 |
|---|---:|---:|---:|---:|---:|---:|
| Momentum | 0.34% | 0.41% | 0.15% | 0.31% | 0.48% | 0.13% |
| Value | 0.04% | 0.42% | 0.36% | 0.48% | 0.48% | 0.44% |
| Quality | -0.17% | 0.45% | 0.25% | 0.48% | 0.76% | 0.93% |
| Low volatility | 0.23% | 0.23% | 0.60% | 0.30% | 0.42% | 0.19% |

Quality has the largest synthetic top-minus-bottom spread, which is expected given the generator. None of these rows should be interpreted as an investable real-market spread, and the middle buckets are not uniformly monotonic.

### 11.3 Composite Portfolio Summary

Default cost assumption: 10 bps per unit of one-way turnover.

| Metric | Synthetic output |
|---|---:|
| Monthly observations | 106 |
| Annualized net return | 10.22% |
| Annualized volatility | 4.54% |
| Zero-risk-free-rate Sharpe | 2.17 |
| Maximum drawdown | -3.67% |
| Positive month ratio | 74.5% |
| Average one-way turnover | 25.63% |
| Arithmetic sum of monthly cost deductions | 2.72% |

The last row is a simple sum of monthly return deductions, not a compounded performance contribution.

### 11.4 Cost Sensitivity

| Cost assumption | Annualized net return | Zero-RF Sharpe | Maximum drawdown |
|---:|---:|---:|---:|
| 0 bps | 10.55% | 2.25 | -3.63% |
| 5 bps | 10.39% | 2.21 | -3.65% |
| 10 bps | 10.22% | 2.17 | -3.67% |
| 20 bps | 9.88% | 2.10 | -3.70% |
| 50 bps | 8.88% | 1.89 | -3.82% |

This table proves only that the accounting responds monotonically to a larger flat cost assumption. It does not establish that any row represents achievable execution.

### 11.5 Benchmark Output

The monthly result file includes `benchmark_return` and `excess_return`, and the equity-curve chart plots the strategy and equal-weight eligible-universe benchmark. The pipeline does not yet export a complete benchmark-relative summary such as tracking error, information ratio, beta, or risk-factor attribution.

## 12. Automated Tests

The current test suite covers fourteen behaviors:

- synthetic data are deterministic for a fixed seed;
- next-month returns do not cross ticker boundaries;
- momentum uses only prior within-ticker prices;
- initial turnover equals full investment;
- constant positive returns produce the expected compounded annual return and no drawdown;
- a negative first month is included in maximum drawdown;
- the composite remains missing until all four factors are available;
- an eligible missing future return raises rather than being dropped;
- a missing calendar month within a ticker is rejected.
- an all-missing future-return intermediate month raises rather than being skipped;
- turnover uses return-drifted pretrade weights rather than prior target weights.
- an undersized eligible universe after portfolio formation raises rather than skipping an intermediate month.
- the official public-factor CSV parser reads only monthly observations and converts percentages to decimals.
- public factor summaries return finite dependence-aware statistics for a declared evaluation sample.

The test suite passes in the current workspace. These tests materially improve implementation reliability, but they do not test whether factors work in real markets.

## 13. Validity Controls Already Implemented

- deterministic seed and reproducible synthetic panel;
- explicit schema, uniqueness, identifier, and price validation;
- explicit consecutive-month validation within ticker;
- within-ticker price lags and future returns;
- one-period lag after the trailing low-volatility calculation;
- latest-month skip in momentum;
- mechanical fundamental lag clearly labeled as a demo convention;
- complete-case four-factor composite;
- missing eligible next-month returns cause a hard failure;
- explicit equal-weight benchmark and monthly excess return;
- one-way turnover with initial investment cost;
- cost sensitivity at 0, 5, 10, 20, and 50 bps;
- Rank IC positive ratio calculated only from valid IC months;
- five-quantile returns and top-minus-bottom summaries;
- initial-wealth-aware maximum drawdown;
- saved IC, IC summary, monthly returns, metrics, sensitivity, and chart artifacts.

## 14. Remaining Limitations

The following items prevent a real alpha or deployability claim:

- no real security-level equity panel has been included or evaluated; the public
  factor returns are constructed aggregate portfolios;
- the three-month fundamental lag is not based on actual publication dates;
- there is no original-vintage or restatement-aware fundamental database;
- inactive and delisted securities and their final returns are not supplied;
- corporate-action and total-return definitions are not documented for real data;
- no chronological train, validation, and untouched test split is implemented;
- no sector, industry, size, beta, leverage, or liquidity neutralization is implemented;
- no historical investable-universe rule, suspension rule, or share-class policy is implemented;
- the benchmark is an internal equal-weight universe, not an external investable index;
- quantile returns are exported, but their turnover, costs, and statistical uncertainty are not;
- the flat basis-point cost model omits spread variation, impact, tax, delay, and capacity;
- no statistical confidence interval, dependence-robust inference, or multiple-testing adjustment is reported;
- dependency ranges are constrained but not locked to exact versions;
- the input-data acquisition and legal redistribution process is not yet documented.

## 15. Real-Data Research Plan

1. Define a historical, investable universe with stable security identifiers.
2. Obtain adjusted prices, corporate actions, inactive securities, and delisting returns.
3. Join fundamentals by actual public release timestamp and preserve revision policy.
4. Add market capitalization, sector, beta, leverage, and liquidity fields.
5. Freeze factor definitions, exclusions, timing, execution, and cost assumptions.
6. Create chronological research, validation, and untouched final-test periods.
7. Run data-timing and universe audits before viewing factor results.
8. Evaluate single-factor Rank IC, confidence intervals, quantile monotonicity, and turnover.
9. Add sector and size neutralization and attribute common risk exposures.
10. Compare the composite with external and exposure-matched benchmarks.
11. Stress execution delay, spread, impact, tax, turnover, and capacity.
12. Open the final test once and report favorable, weak, and failed results together.

## 16. Reproduction

From the repository root:

```powershell
python -m pip install -r requirements.txt
python run_research.py
python -m pytest -q
```

Optional arguments:

```powershell
python run_research.py --seed 11 --cost-bps 20
python run_research.py --input path\to\monthly_panel.csv --output-dir results\real_data_trial
```

Supplying a CSV does not make a run point-in-time or unbiased. The researcher must independently establish data provenance, publication timing, universe history, adjustment policy, and delisting treatment.

Expected output artifacts:

```text
results/
|-- monthly_returns.csv
|-- factor_ic.csv
|-- factor_ic_summary.csv
|-- factor_quantile_returns.csv
|-- factor_quantile_summary.csv
|-- metrics.csv
|-- cost_sensitivity.csv
`-- equity_curve.png
```

## Conclusion

The project is now a coherent and test-covered research scaffold. It implements Rank IC, a basic benchmark, one-way turnover costs, cost sensitivity, performance metrics, and reproducible outputs while correcting important defects from the initial prototype.

Its correct current interpretation remains narrow: the repository demonstrates how to structure and audit a multi-factor workflow on synthetic data. Evidence of market alpha requires the real-data controls, out-of-sample design, neutralization, and execution analysis described above.

This project is for research and education only and is not investment advice.
