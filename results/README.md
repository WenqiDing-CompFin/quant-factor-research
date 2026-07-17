# Generated Results

All committed results in this directory come from the deterministic synthetic
demo and are not evidence of real-market alpha.

- `metrics.csv`: portfolio summary statistics.
- `monthly_returns.csv`: signal-date portfolio, benchmark, cost, and turnover data.
- `factor_ic.csv`: monthly single-factor Rank IC observations.
- `factor_ic_summary.csv`: mean IC, IC dispersion, positive ratio, and ICIR.
- `factor_quantile_returns.csv`: monthly next-period returns for five factor buckets.
- `factor_quantile_summary.csv`: average bucket returns and top-minus-bottom spread.
- `cost_sensitivity.csv`: results under multiple linear cost assumptions.
- `equity_curve.png`: growth of one synthetic dollar versus the equal-weight universe.

Regenerate all files from the repository root with:

```bash
python run_research.py
```
