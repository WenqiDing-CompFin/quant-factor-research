"""Long-only cross-sectional portfolio backtest."""

from __future__ import annotations

import pandas as pd


def _one_way_turnover(previous: dict[str, float], current: dict[str, float]) -> float:
    if not previous:
        return sum(current.values())
    names = set(previous).union(current)
    return 0.5 * sum(abs(current.get(name, 0.0) - previous.get(name, 0.0)) for name in names)


def backtest_top_quantile(
    panel: pd.DataFrame,
    top_fraction: float = 0.20,
    cost_bps: float = 10.0,
    min_stocks: int = 20,
) -> pd.DataFrame:
    """Hold the highest composite-score stocks for the next month.

    Costs are applied to one-way turnover. Missing next-month returns among
    selected stocks raise an error to avoid silently introducing survivor bias.
    """
    if not 0 < top_fraction <= 1:
        raise ValueError("top_fraction must be in (0, 1].")
    if cost_bps < 0:
        raise ValueError("cost_bps cannot be negative.")
    if min_stocks < 2:
        raise ValueError("min_stocks must be at least 2.")

    pretrade_weights: dict[str, float] = {}
    final_date = panel["date"].max()
    backtest_started = False
    rows = []
    for date, cross_section in panel.groupby("date", sort=True):
        eligible = cross_section.dropna(subset=["composite_score"])
        if len(eligible) < min_stocks:
            if backtest_started:
                raise ValueError(
                    f"Eligible universe fell below {min_stocks} on {date}; "
                    "refusing to skip an intermediate holding period."
                )
            continue
        if eligible["future_return_1m"].isna().all():
            if date == final_date:
                continue
            raise ValueError(
                f"All future returns are missing on non-final date {date}."
            )
        if eligible["future_return_1m"].isna().any():
            missing_names = eligible.loc[
                eligible["future_return_1m"].isna(), "ticker"
            ].tolist()
            raise ValueError(
                f"Missing future returns on {date} for eligible stocks: "
                f"{missing_names[:5]}. Supply delisting/next-period returns."
            )
        n_select = max(1, int(len(eligible) * top_fraction))
        selected = eligible.nlargest(n_select, "composite_score").copy()
        weight = 1.0 / n_select
        current_weights = dict.fromkeys(selected["ticker"], weight)
        turnover = _one_way_turnover(pretrade_weights, current_weights)
        gross_return = float(selected["future_return_1m"].mean())
        benchmark_return = float(eligible["future_return_1m"].mean())
        trading_cost = turnover * cost_bps / 10_000.0
        rows.append(
            {
                "signal_date": date,
                "gross_return": gross_return,
                "net_return": gross_return - trading_cost,
                "benchmark_return": benchmark_return,
                "excess_return": gross_return - trading_cost - benchmark_return,
                "turnover": turnover,
                "trading_cost": trading_cost,
                "n_eligible": len(eligible),
                "n_selected": n_select,
            }
        )
        backtest_started = True
        end_values = {
            row.ticker: weight * (1.0 + row.future_return_1m)
            for row in selected[["ticker", "future_return_1m"]].itertuples(index=False)
        }
        total_end_value = sum(end_values.values())
        pretrade_weights = {
            ticker: value / total_end_value for ticker, value in end_values.items()
        }
    return pd.DataFrame.from_records(rows)
