"""Point-in-time factor construction and factor diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import validate_panel


FACTOR_COLUMNS = ("momentum", "value", "quality", "low_volatility")


def _winsorized_zscore(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if len(valid) < 3:
        return pd.Series(np.nan, index=series.index, dtype=float)
    lower, upper = valid.quantile([0.01, 0.99])
    clipped = series.clip(lower, upper)
    scale = clipped.std(ddof=0)
    if pd.isna(scale) or scale == 0:
        return pd.Series(np.nan, index=series.index, dtype=float)
    return (clipped - clipped.mean()) / scale


def build_factor_panel(df: pd.DataFrame, fundamental_lag_months: int = 3) -> pd.DataFrame:
    """Build monthly signals available at each month end.

    Momentum is P(t-1) / P(t-12) - 1, which skips the most recent month.
    Fundamentals are mechanically lagged as a conservative demo convention. A
    production study must use actual publication timestamps instead.
    """
    validate_panel(df)
    if fundamental_lag_months < 0:
        raise ValueError("fundamental_lag_months cannot be negative.")

    panel = df.sort_values(["ticker", "date"]).copy()
    grouped_close = panel.groupby("ticker", sort=False)["close"]
    panel["return_1m"] = grouped_close.pct_change(fill_method=None)
    panel["future_return_1m"] = grouped_close.shift(-1).div(panel["close"]).sub(1)
    panel["momentum"] = grouped_close.shift(1).div(grouped_close.shift(12)).sub(1)
    panel["realized_volatility_12m"] = panel.groupby("ticker", sort=False)[
        "return_1m"
    ].transform(lambda values: values.rolling(12, min_periods=12).std(ddof=1).shift(1))
    panel["low_volatility"] = -panel["realized_volatility_12m"]
    panel["value"] = panel.groupby("ticker", sort=False)["book_to_market"].shift(
        fundamental_lag_months
    )
    panel["quality"] = panel.groupby("ticker", sort=False)["roe"].shift(
        fundamental_lag_months
    )

    z_columns = []
    for factor in FACTOR_COLUMNS:
        z_name = f"{factor}_z"
        panel[z_name] = panel.groupby("date", sort=False)[factor].transform(
            _winsorized_zscore
        )
        z_columns.append(z_name)
    panel["composite_score"] = panel[z_columns].sum(
        axis=1, min_count=len(z_columns)
    ) / len(z_columns)
    return panel


def _rank_correlation(group: pd.DataFrame, factor: str) -> float:
    usable = group[[factor, "future_return_1m"]].dropna()
    if len(usable) < 3:
        return float("nan")
    factor_rank = usable[factor].rank(method="average")
    return_rank = usable["future_return_1m"].rank(method="average")
    return float(factor_rank.corr(return_rank))


def compute_factor_ic(
    panel: pd.DataFrame, factors: tuple[str, ...] = FACTOR_COLUMNS
) -> pd.DataFrame:
    records = []
    for date, cross_section in panel.groupby("date", sort=True):
        row: dict[str, object] = {"date": date}
        for factor in factors:
            row[factor] = _rank_correlation(cross_section, factor)
        records.append(row)
    return pd.DataFrame.from_records(records)


def compute_quantile_returns(
    panel: pd.DataFrame,
    factors: tuple[str, ...] = FACTOR_COLUMNS,
    quantiles: int = 5,
) -> pd.DataFrame:
    """Calculate equal-weight next-month returns by factor quantile and date."""
    if quantiles < 2:
        raise ValueError("quantiles must be at least 2.")
    records = []
    for date, cross_section in panel.groupby("date", sort=True):
        for factor in factors:
            usable = cross_section[[factor, "future_return_1m"]].dropna().copy()
            if len(usable) < quantiles * 2:
                continue
            ranks = usable[factor].rank(method="first")
            usable["quantile"] = pd.qcut(ranks, q=quantiles, labels=False) + 1
            means = usable.groupby("quantile")["future_return_1m"].mean()
            row: dict[str, object] = {"date": date, "factor": factor}
            for quantile, value in means.items():
                row[f"q{int(quantile)}"] = float(value)
            row["top_minus_bottom"] = float(means.loc[quantiles] - means.loc[1])
            records.append(row)
    return pd.DataFrame.from_records(records)
