"""Data generation, loading, and validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"date", "ticker", "close", "book_to_market", "roe"}


def generate_synthetic_panel(
    seed: int = 7, n_stocks: int = 100, months: int = 120
) -> pd.DataFrame:
    """Create deterministic monthly data for pipeline testing only.

    The generated returns include simple latent exposures. They are not calibrated
    to a real market and cannot be used as evidence of an investable strategy.
    """
    if n_stocks < 20 or months < 24:
        raise ValueError("Use at least 20 stocks and 24 months for the demo panel.")

    rng = np.random.default_rng(seed)
    dates = pd.date_range("2015-01-31", periods=months, freq=pd.offsets.MonthEnd())
    tickers = [f"S{i:04d}" for i in range(n_stocks)]
    value = rng.normal(size=n_stocks)
    quality = rng.normal(size=n_stocks)
    idio_vol = rng.uniform(0.035, 0.085, size=n_stocks)
    prices = np.full(n_stocks, 100.0)
    previous_return = np.zeros(n_stocks)
    records: list[dict[str, object]] = []

    for date in dates:
        monthly_return = (
            0.004
            + 0.0025 * value
            + 0.0030 * quality
            + 0.10 * previous_return
            + rng.normal(0.0, idio_vol)
        )
        monthly_return = np.clip(monthly_return, -0.60, 0.60)
        prices *= 1.0 + monthly_return
        for i, ticker in enumerate(tickers):
            records.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "close": prices[i],
                    "book_to_market": np.exp(0.20 * value[i] + rng.normal(0, 0.08)),
                    "roe": 0.12 + 0.035 * quality[i] + rng.normal(0, 0.01),
                }
            )
        previous_return = monthly_return

    return pd.DataFrame.from_records(records)


def validate_panel(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Input panel is empty.")
    if df[["date", "ticker"]].duplicated().any():
        raise ValueError("Each date/ticker pair must be unique.")
    if df["date"].isna().any() or df["ticker"].isna().any():
        raise ValueError("date and ticker cannot contain missing values.")
    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.isna().any():
        raise ValueError("date must contain valid calendar dates.")
    if (df["close"].dropna() <= 0).any():
        raise ValueError("close must be positive when present.")
    ordered = df.assign(_validated_date=dates).sort_values(["ticker", "_validated_date"])
    for ticker, ticker_dates in ordered.groupby("ticker", sort=False)["_validated_date"]:
        month_number = ticker_dates.dt.year * 12 + ticker_dates.dt.month
        if month_number.diff().dropna().ne(1).any():
            raise ValueError(
                f"Monthly observations for {ticker} must be consecutive; "
                "missing or duplicate months would change the return horizon."
            )


def load_panel(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    validate_panel(df)
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)
