# Project Introduction

## One-Sentence Version

I built a reproducible Python pipeline that constructs four monthly equity factors, evaluates Rank IC and five-quantile returns, forms a top-quintile portfolio against an equal-weight benchmark, applies drift-aware one-way-turnover costs, and exports auditable synthetic research results with twelve automated tests.

## 30-Second Interview Version

This project demonstrates the complete mechanics of monthly cross-sectional factor research. It creates or loads a stock panel, validates consecutive monthly observations, builds 12-to-1 momentum, value, quality, and lagged low-volatility signals, applies a three-month demo lag to fundamentals, and normalizes each factor within the monthly universe. I evaluate the signals with Rank IC and five-quantile returns, combine them into an equal-weight score, hold the top 20%, compare the net portfolio with an equal-weight benchmark, and rerun the strategy across five cost assumptions. The default dataset is synthetic and contains planted relationships, so I present its results as reproducibility checks rather than evidence of market alpha.

## Two-Minute Interview Version

The project began with a practical question: how do I turn several factor hypotheses into a research process that another person can inspect and rerun? I implemented four signals. Momentum uses the price at `t-1` relative to `t-12`, value uses book-to-market, quality uses ROE, and low volatility is the negative of trailing 12-month realized volatility. Value and quality are shifted by three months as a conservative simulation convention. Within every month, the code clips the 1st and 99th percentile tails, calculates z-scores, and requires all four standardized values before producing the composite score.

The diagnostic layer calculates monthly Rank IC for each factor and summarizes its mean, standard deviation, valid-observation positive ratio, observation count, and ICIR. It also reports Q1-Q5 equal-weight next-month returns and the Q5-minus-Q1 spread. The portfolio layer selects the top quintile, equal-weights the names, computes weight-based one-way turnover, deducts transaction costs, and compares the resulting net return with the gross equal-weight eligible-universe benchmark. The runner automatically evaluates 0, 5, 10, 20, and 50 bps cost assumptions and exports seven CSV files plus an equity-curve chart.

I also wrote twelve tests around the failure modes that concern me most at this stage: deterministic generation, return leakage across securities, momentum lookback timing across multiple tickers, composite completeness, partial and all-missing future returns, gaps in monthly observations, post-start universe coverage, initial and drift-aware turnover, annualization, and first-period drawdown. The backtest raises an error when an otherwise eligible security is missing its next-period return, rather than silently dropping it and introducing a survivor-style bias.

The most important boundary is that all committed evidence is synthetic. The generator deliberately links returns to latent value and quality characteristics and includes short-term persistence. A uniform three-month lag is not equivalent to real filing timestamps, and the monthly close-to-close convention is not execution-level modeling. I therefore use the project to demonstrate research design, code auditability, and awareness of bias. A real empirical claim would require point-in-time public or licensed data, delisting returns, exposure controls, an explicit execution rule, and a locked out-of-sample period.

## Likely Interview Follow-Ups

### Did the strategy generate alpha?

The repository cannot support that conclusion. The included figures come from a synthetic generator with planted structure. They show that the pipeline responds coherently to known simulated relationships, not that the strategy earns historical or live alpha.

### Why use Rank IC?

The strategy makes a cross-sectional ranking decision, so Rank IC directly checks whether higher factor ranks align with higher next-month return ranks. It is less dependent on the scale of the raw factor and returns than a linear correlation. I still need a much broader inference framework before making an empirical claim.

### How is turnover calculated?

It is one-way weight turnover: one half of the sum of absolute changes across the union of prior and current portfolio weights. The first portfolio has turnover of 100%, reflecting initial investment.

### Why lag fundamentals by three months?

It prevents the demo from using same-row accounting values immediately. However, it is only a conservative mechanical rule. Real research should align each filing with its actual publication timestamp and handle restatements explicitly.

### What benchmark is used?

The benchmark is the equal-weight next-month return of all securities eligible for scoring on the signal date. The portfolio is reported net of its modeled trading cost, while the benchmark is gross, which is a documented limitation.

### What do the tests prove?

They verify twelve specific implementation invariants. They do not prove the factor hypothesis, fully validate execution timing, eliminate all leakage risk, or substitute for data and research review.

### What would you do next?

I would move to legally usable point-in-time data, define the universe and next-session execution convention before inspecting results, add delisting returns and exposure diagnostics, and lock a final test period. I would also publish negative subperiod and parameter results, not only the strongest specification.

## Maintainer

[WenqiDing-CompFin](https://github.com/WenqiDing-CompFin)
