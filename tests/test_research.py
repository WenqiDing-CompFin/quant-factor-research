from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_factor import (  # noqa: E402
    backtest_top_quantile,
    build_factor_panel,
    generate_synthetic_panel,
    performance_metrics,
    validate_panel,
)


def test_synthetic_data_is_deterministic():
    first = generate_synthetic_panel(seed=11, n_stocks=20, months=24)
    second = generate_synthetic_panel(seed=11, n_stocks=20, months=24)
    pd.testing.assert_frame_equal(first, second)


def test_future_return_does_not_cross_tickers():
    raw = generate_synthetic_panel(seed=2, n_stocks=20, months=24)
    panel = build_factor_panel(raw)
    last_rows = panel.groupby("ticker").tail(1)
    assert last_rows["future_return_1m"].isna().all()


def test_momentum_uses_only_prior_prices():
    raw = generate_synthetic_panel(seed=3, n_stocks=20, months=24)
    panel = build_factor_panel(raw)
    stock = panel[panel["ticker"] == "S0000"].reset_index(drop=True)
    expected = stock.loc[11, "close"] / stock.loc[0, "close"] - 1
    assert stock.loc[12, "momentum"] == pytest.approx(expected)
    second_stock = panel[panel["ticker"] == "S0001"].reset_index(drop=True)
    second_expected = second_stock.loc[11, "close"] / second_stock.loc[0, "close"] - 1
    assert second_stock.loc[12, "momentum"] == pytest.approx(second_expected)


def test_first_turnover_is_full_investment():
    raw = generate_synthetic_panel(seed=4, n_stocks=30, months=36)
    monthly = backtest_top_quantile(build_factor_panel(raw), min_stocks=20)
    assert monthly.iloc[0]["turnover"] == pytest.approx(1.0)


def test_metrics_match_constant_positive_returns():
    metrics = performance_metrics(pd.Series([0.01] * 12))
    assert metrics["annual_return"] == pytest.approx(1.01**12 - 1)
    assert np.isnan(metrics["sharpe_zero_rf"])
    assert metrics["max_drawdown"] == pytest.approx(0.0)


def test_drawdown_includes_a_negative_first_month():
    metrics = performance_metrics(pd.Series([-0.10, 0.05]))
    assert metrics["max_drawdown"] == pytest.approx(-0.10)


def test_composite_requires_all_four_factors():
    raw = generate_synthetic_panel(seed=5, n_stocks=20, months=24)
    panel = build_factor_panel(raw)
    stock = panel[panel["ticker"] == "S0000"].reset_index(drop=True)
    assert stock.loc[:12, "composite_score"].isna().all()
    assert pd.notna(stock.loc[13, "composite_score"])


def test_missing_future_return_is_not_silently_dropped():
    raw = generate_synthetic_panel(seed=6, n_stocks=30, months=36)
    panel = build_factor_panel(raw)
    target_index = panel[panel["composite_score"].notna()].index[0]
    panel.loc[target_index, "future_return_1m"] = np.nan
    with pytest.raises(ValueError, match="Missing future returns"):
        backtest_top_quantile(panel, min_stocks=20)


def test_monthly_gap_is_rejected():
    raw = generate_synthetic_panel(seed=8, n_stocks=20, months=24)
    second_month = sorted(raw["date"].unique())[1]
    with_gap = raw[~((raw["ticker"] == "S0000") & (raw["date"] == second_month))]
    with pytest.raises(ValueError, match="must be consecutive"):
        validate_panel(with_gap)


def test_all_missing_future_returns_on_intermediate_date_raise():
    raw = generate_synthetic_panel(seed=9, n_stocks=30, months=36)
    panel = build_factor_panel(raw)
    eligible_dates = panel.loc[panel["composite_score"].notna(), "date"].unique()
    target_date = eligible_dates[1]
    panel.loc[panel["date"] == target_date, "future_return_1m"] = np.nan
    with pytest.raises(ValueError, match="All future returns"):
        backtest_top_quantile(panel, min_stocks=20)


def test_turnover_accounts_for_weight_drift():
    dates = pd.to_datetime(["2020-01-31", "2020-02-29", "2020-03-31"])
    rows = []
    for date_index, date in enumerate(dates):
        for ticker, score in zip(["A", "B", "C", "D"], [4.0, 3.0, 2.0, 1.0]):
            future_return = np.nan
            if date_index == 0:
                future_return = 1.0 if ticker == "A" else 0.0
            elif date_index == 1:
                future_return = 0.0
            rows.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "composite_score": score,
                    "future_return_1m": future_return,
                }
            )
    monthly = backtest_top_quantile(
        pd.DataFrame(rows), top_fraction=0.5, cost_bps=0, min_stocks=4
    )
    assert monthly.iloc[0]["turnover"] == pytest.approx(1.0)
    assert monthly.iloc[1]["turnover"] == pytest.approx(1.0 / 6.0)


def test_low_eligibility_after_start_is_not_silently_skipped():
    raw = generate_synthetic_panel(seed=10, n_stocks=30, months=36)
    panel = build_factor_panel(raw)
    eligible_dates = panel.loc[panel["composite_score"].notna(), "date"].unique()
    target_date = eligible_dates[2]
    target_rows = panel.index[panel["date"] == target_date][:15]
    panel.loc[target_rows, "composite_score"] = np.nan
    with pytest.raises(ValueError, match="Eligible universe fell below"):
        backtest_top_quantile(panel, min_stocks=20)
