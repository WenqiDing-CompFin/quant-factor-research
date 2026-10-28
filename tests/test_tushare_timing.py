"""Offline checks for the daily A-share adapter and its backtest frequency."""

import importlib.util
import sys
from argparse import Namespace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from data.tushare_data_loader import _build_ticker_panel, _load_trading_dates
from quant_factor import backtest_top_quantile


def test_missing_session_is_not_bridged_or_dropped():
    dates = pd.bdate_range("2023-01-02", periods=24)
    bars = pd.DataFrame(
        {
            "trade_date": dates.strftime("%Y%m%d"),
            "ts_code": "A.SH",
            "close": np.arange(100.0, 124.0),
            "vol": 1,
        }
    ).drop(index=21)
    one = _build_ticker_panel(bars, "A.SH", dates)
    assert one.loc[20, "factor_value"] == pytest.approx(120 / 100 - 1)
    assert pd.isna(one.loc[20, "return"])
    assert pd.isna(one.loc[21, "close"])
    assert pd.isna(one.loc[23, "return"])
    two = one.assign(ticker="B.SH", asset_id="B.SH")
    with pytest.raises(ValueError, match="future returns"):
        backtest_top_quantile(pd.concat([one, two]), min_stocks=2)


def test_calendar_requires_complete_calendar_dates(monkeypatch):
    calendar = pd.DataFrame({"cal_date": ["20230102", "20230104"], "is_open": [1, 1]})

    class Provider:
        def trade_cal(self, **kwargs):
            return calendar

    monkeypatch.setattr("data.tushare_data_loader.RATE_LIMIT_SECONDS", 0)
    with pytest.raises(ValueError, match="does not cover"):
        _load_trading_dates(Provider(), "20230102", "20230104")


def test_real_example_annualizes_daily_not_monthly(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "real_example", ROOT / "examples/run_real_data_backtest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dates = pd.bdate_range("2023-01-02", periods=25)
    frames = []
    for i in range(20):
        bars = pd.DataFrame(
            {
                "trade_date": dates.strftime("%Y%m%d"),
                "ts_code": f"A{i}.SH",
                "close": 100 * 1.001 ** np.arange(len(dates)),
                "vol": 1,
            }
        )
        frames.append(_build_ticker_panel(bars, f"A{i}.SH", dates))
    monkeypatch.setattr(
        module, "load_real_a_share_panel", lambda *args, **kwargs: pd.concat(frames)
    )
    args = Namespace(
        start_date="20230102",
        end_date="20230203",
        sample_size=20,
        top_fraction=0.2,
        cost_bps=0,
        min_stocks=20,
    )
    _, _, _, backtest, metrics = module.run_real(args)
    assert len(backtest) == 4
    assert metrics["annual_return"] == pytest.approx(1.001**252 - 1)
    assert "positive_period_ratio" in metrics
    assert "positive_month_ratio" not in metrics
