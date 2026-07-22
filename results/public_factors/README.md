# Official Public Factor Data

`official_current_snapshot.csv` records the current-return table published by
the Kenneth French Data Library as of May 2026. Values are percentages reported
by the source for one month, the last three months, and the last twelve months.
They were checked against the official page on 2026-07-22.

The snapshot is a small, reviewable real-data artifact. For the full monthly
history, run:

```bash
python run_public_factor_validation.py
```

The command downloads the official five-factor and momentum archives into the
ignored `data/raw/fama_french/` cache and writes generated analysis to the
ignored `results/public_factors/generated/` directory. Its metadata records the
official URLs and SHA-256 hashes of both downloaded archives.

These are constructed U.S. factor portfolios. They are not security-level data,
not results from this repository's composite stock strategy, and not evidence
that the synthetic stock backtest earns market alpha.
