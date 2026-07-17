# Data Contract

The default demo does not require a downloaded dataset. `run_research.py`
generates a deterministic synthetic monthly panel from a fixed random seed.
Synthetic observations exist only to test the pipeline.

An external CSV must contain one unique row per `date` and `ticker`:

| Column | Type | Required meaning |
|---|---|---|
| `date` | date | Month-end signal observation date |
| `ticker` | string | Stable security identifier |
| `close` | positive float | Consistently adjusted closing price |
| `book_to_market` | float | Value input known under the chosen availability rule |
| `roe` | float | Quality input known under the chosen availability rule |

The code applies a three-month mechanical lag to fundamental columns. This is
only a conservative demo rule; real research must join fundamentals using their
actual publication timestamps and revision vintages.

Never commit employer data, vendor-licensed data, credentials, client details,
or proprietary strategy inputs. `data/raw/` and `data/private/` are ignored by
Git by default.
