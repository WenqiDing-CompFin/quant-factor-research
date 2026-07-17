# Reproducible Multi-Factor Equity Research

[WenqiDing-CompFin](https://github.com/WenqiDing-CompFin) maintains this educational Python project for auditable, monthly cross-sectional equity research.

> **Synthetic-data boundary:** the default dataset is simulated and deliberately links returns to latent value, quality, and momentum structure. The included performance and IC values validate the research pipeline; they are not historical-market evidence, market alpha, or an investable result. Nothing in this repository is investment advice.

## What the Project Does

The repository implements an end-to-end research baseline:

- deterministic generation of 100 synthetic stocks over 120 monthly observations;
- validation of required columns, valid dates, unique `(date, ticker)` keys, positive prices, and consecutive monthly observations within each ticker;
- 12-to-1 momentum, book-to-market value, ROE quality, and trailing low-volatility signals;
- a conservative three-month demo lag for fundamental variables;
- monthly cross-sectional 1st/99th percentile winsorization and z-score normalization;
- an equal-weight composite requiring all four factor scores;
- factor Rank IC, IC standard deviation, valid-observation positive-IC ratio, ICIR, and five-quantile return diagnostics;
- a top-20% equal-weight long-only portfolio and equal-weight eligible-universe benchmark;
- weight-based one-way turnover and configurable transaction costs;
- 0/5/10/20/50 bps cost-sensitivity analysis;
- portfolio return, volatility, zero-risk-free-rate Sharpe ratio, drawdown, hit-rate, turnover, and cost outputs;
- twelve automated tests covering determinism, ticker boundaries, signal timing, composite eligibility, missing future returns, monthly continuity, universe coverage, drift-aware turnover, annualization, and drawdown;
- reproducible CSV results and an equity-curve chart written to `results/`.

## Research Question

Can a transparent combination of momentum, value, quality, and low-volatility characteristics produce a stable cross-sectional ranking after explicit timing, turnover, benchmark, and transaction-cost controls?

The current repository answers this question only inside a controlled synthetic experiment. Moving from pipeline validation to an empirical market conclusion requires licensed or redistributable historical data with real publication timestamps, delisting returns, and documented universe membership.

## Factor Definitions

| Factor | Implementation at signal month `t` | Direction |
|---|---|---:|
| Momentum | `close[t-1] / close[t-12] - 1` | Higher is better |
| Value | `book_to_market` shifted by 3 monthly rows per ticker | Higher is better |
| Quality | `roe` shifted by 3 monthly rows per ticker | Higher is better |
| Low volatility | Negative trailing 12-month return volatility ending at `t-1` | Higher is better |

The momentum signal skips the most recent month. The three-month fundamental lag is a transparent demo convention, not a substitute for actual filing publication timestamps. A real-data study must use the information that was genuinely available on each decision date.

## Research Pipeline

1. Generate the fixed-seed synthetic panel or load an external monthly CSV.
2. Validate the data contract and sort each security chronologically.
3. Build one-month future returns without crossing ticker boundaries.
4. Construct the four lagged signals.
5. Winsorize and standardize each signal within each month.
6. Average all four z-scores into a composite; incomplete rows remain ineligible.
7. Calculate monthly factor Rank IC against next-month returns and split each raw factor into five equal-count rank quantiles.
8. Export each quantile's equal-weight next-month return and the top-minus-bottom spread.
9. Select the top 20% of composite-score names and assign equal weights.
10. Drift prior holdings by their realized returns, then calculate one-way turnover as `0.5 * sum(abs(target_weight - pretrade_weight))`; initial investment turnover is 100%.
11. Deduct `turnover * cost_bps / 10,000` from portfolio return.
12. Compare net portfolio return with the gross equal-weight return of the same eligible universe.
13. Export portfolio, factor, quantile, cost-sensitivity, metric, and chart artifacts.

Rank IC is computed as the correlation between cross-sectional factor ranks and next-month return ranks. The positive-IC ratio uses only non-missing monthly IC observations. The reported ICIR is mean Rank IC divided by its sample standard deviation; it is not annualized. Quantile assignment ranks ties deterministically, applies `qcut` to create five groups, and defines the spread as Q5 minus Q1.

## Repository Layout

```text
quant-factor-research/
|-- README.md
|-- requirements.txt
|-- run_research.py
|-- docs/
|   |-- factor_research_report.md
|   |-- failure_analysis.md
|   |-- project_introduction.md
|   |-- resume_bullets.md
|   `-- logs/
|       |-- daily_report_template.md
|       `-- weekly_report_template.md
|-- results/
|   |-- cost_sensitivity.csv
|   |-- equity_curve.png
|   |-- factor_ic.csv
|   |-- factor_ic_summary.csv
|   |-- factor_quantile_returns.csv
|   |-- factor_quantile_summary.csv
|   |-- metrics.csv
|   `-- monthly_returns.csv
|-- src/
|   `-- quant_factor/
|       |-- __init__.py
|       |-- backtest.py
|       |-- data.py
|       |-- factors.py
|       `-- metrics.py
`-- tests/
    `-- test_research.py
```

## Installation

From the repository root:

```bash
python -m venv .venv
```

Activate the environment, then install the pinned dependency ranges:

```bash
python -m pip install -r requirements.txt
```

Required packages are NumPy, pandas, Matplotlib, and pytest. Python 3.10 or later is recommended.

## Reproduce the Synthetic Baseline

Run the full pipeline from the repository root:

```bash
python run_research.py
```

Run the tests:

```bash
python -m pytest -q
```

Expected test summary:

```text
12 passed
```

Change the transaction-cost assumption or synthetic seed:

```bash
python run_research.py --cost-bps 20 --seed 11
```

Write outputs to a separate experiment directory:

```bash
python run_research.py --output-dir results/seed_11 --seed 11
```

## Run With an External Panel

```bash
python run_research.py --input data/public_monthly_panel.csv
```

The input CSV must contain:

| Column | Type | Requirement |
|---|---|---|
| `date` | date | Monthly observation date; cannot be missing |
| `ticker` | string | Stable security identifier; cannot be missing |
| `close` | float | Positive when present; consistently adjusted |
| `book_to_market` | float | Fundamental value proxy |
| `roe` | float | Fundamental quality proxy |

Each `(date, ticker)` pair must be unique, and each ticker's observations must advance by exactly one calendar month. A missing month raises an error because row-based lags would otherwise change the intended return horizon. The loader checks schema and basic integrity, but the user remains responsible for corporate-action adjustment, publication timing, delisting returns, survivorship, universe construction, and redistribution rights.

Do not commit employer data, paid vendor data, confidential code, client information, API keys, proprietary parameters, or internal screenshots.

## Generated Results

`python run_research.py` writes:

| File | Contents |
|---|---|
| `results/monthly_returns.csv` | Signal date, gross/net/benchmark/excess returns, turnover, cost, and universe counts |
| `results/factor_ic.csv` | Monthly Rank IC for each raw factor |
| `results/factor_ic_summary.csv` | Mean Rank IC, IC standard deviation, positive ratio, observation count, and ICIR |
| `results/factor_quantile_returns.csv` | Monthly Q1-Q5 next-month returns and top-minus-bottom spread by factor |
| `results/factor_quantile_summary.csv` | Time-series mean of each factor's quantile returns and spread |
| `results/metrics.csv` | Net portfolio summary metrics and synthetic-data flag |
| `results/cost_sensitivity.csv` | Performance at 0/5/10/20/50 bps |
| `results/equity_curve.png` | Growth of one dollar for the portfolio and benchmark |

### Default Seed-7 Synthetic Check

The committed artifacts currently report the following 10 bps synthetic baseline:

| Metric | Synthetic result |
|---|---:|
| Evaluated months | 106 |
| Annualized return | 10.22% |
| Annualized volatility | 4.54% |
| Sharpe ratio, zero risk-free rate | 2.17 |
| Maximum drawdown | -3.67% |
| Positive-month ratio | 74.53% |
| Average one-way turnover | 25.63% |

The synthetic generator explicitly loads returns on latent value and quality characteristics and includes short-term return persistence. These numbers are therefore expected pipeline behavior, not evidence that the factor combination works in a real market. Do not use them as performance claims in a resume, application essay, or interview.

The factor diagnostics reinforce that boundary: in the default simulation, mean Rank IC is approximately 0.0016 for momentum, 0.0248 for value, 0.0427 for quality, and 0.0111 for low volatility. They describe this specific simulation only.

### Cost Sensitivity

The pipeline reruns the complete portfolio calculation at five cost assumptions. For the committed synthetic seed, annualized return declines from 10.55% at 0 bps to 8.88% at 50 bps. This is a mechanical sensitivity check, not a calibrated estimate of real commissions, spread, impact, taxes, or capacity.

## Test Coverage

The twelve tests verify that:

1. synthetic generation is deterministic for a fixed seed;
2. future returns do not leak across ticker boundaries;
3. momentum uses only the intended prior prices;
4. initial one-way turnover equals full investment;
5. annualized return matches a hand-checkable constant-return case;
6. drawdown includes a negative first month;
7. the composite remains unavailable until all four factor values exist;
8. a missing future return among eligible names raises an error instead of being silently dropped;
9. a missing monthly row within a ticker is rejected before row-based lags are calculated;
10. an intermediate month with no future returns raises instead of being skipped;
11. turnover compares target weights with return-drifted pretrade weights.
12. an undersized eligible universe after the backtest starts raises instead of silently skipping a holding period.

The tests reduce implementation risk but do not validate the economic hypothesis or prove the absence of every form of leakage.

## Known Limitations

- All committed results are synthetic-only.
- The simulation has no delistings, index changes, trading halts, corporate actions, liquidity limits, or market-capacity constraints.
- A uniform three-month accounting lag is only a demo approximation to real publication timing.
- Signals use information ending at `t-1` or earlier, but the monthly model assumes rebalancing at the `t` close and does not simulate next-session prices, spread, or slippage.
- The equal-weight benchmark is gross of its own rebalancing costs, while portfolio excess return uses the net strategy return.
- No industry, size, beta, or country neutralization is applied.
- There is no train/validation/test split because the current dataset is a pipeline simulation, not a fitted predictive model.
- Costs are linear in turnover and omit spread, nonlinear impact, borrow, tax, and capacity effects.
- IC inference does not include Newey-West errors, multiple-testing correction, or regime analysis.

## Next Research Stage

The code pipeline is complete for its synthetic educational scope. The next empirical stage is to:

- source legally usable historical data with point-in-time fundamentals and delisting returns;
- define an investable universe and explicit next-session execution rule;
- add statistical inference, stability checks, and cost attribution for factor-quantile spreads, plus benchmark-cost diagnostics;
- measure industry, size, beta, and liquidity exposures;
- lock train, validation, and test periods before parameter selection;
- test subperiod, regime, parameter, and capacity sensitivity;
- document failed hypotheses alongside successful ones.

## Maintainer

[WenqiDing-CompFin](https://github.com/WenqiDing-CompFin)

## Disclaimer

This repository is for education and portfolio demonstration only. It is not financial advice, a solicitation, or a claim of live trading performance.
