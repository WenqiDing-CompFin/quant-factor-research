from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_factor.public_data import (  # noqa: E402
    momentum_decile_validation,
    parse_french_monthly_csv,
    parse_french_portfolio_block,
    public_factor_summary,
)


def test_public_factor_parser_reads_only_monthly_block():
    fixture = """Data Library fixture\n,Mkt-RF,SMB,HML,RMW,CMA,RF\n199001,1.00,2.00,-3.00,4.00,5.00,0.50\n199002,-2.00,1.00,2.00,3.00,4.00,0.40\n\n Annual Factors: January-December\n1990,12.0,0,0,0,0,0\n"""
    parsed = parse_french_monthly_csv(
        fixture, ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
    )
    assert list(parsed["date"]) == [pd.Timestamp("1990-01-31"), pd.Timestamp("1990-02-28")]
    assert parsed.loc[0, "Mkt-RF"] == pytest.approx(0.01)
    assert parsed.loc[0, "HML"] == pytest.approx(-0.03)


def test_public_factor_summary_reports_dependence_aware_statistics():
    dates = pd.date_range("1990-01-31", periods=36, freq="ME")
    frame = pd.DataFrame({"date": dates})
    base = np.tile(np.array([-0.01, 0.005, 0.02]), 12)
    for offset, factor in enumerate(
        ("market_excess", "size", "value", "profitability", "investment", "momentum")
    ):
        frame[factor] = base + offset * 0.0005
    summary = public_factor_summary(frame)
    assert set(summary["factor"]) == {
        "market_excess", "size", "value", "profitability", "investment", "momentum"
    }
    assert summary["observations"].eq(36).all()
    assert np.isfinite(summary["newey_west_mean_tstat"]).all()


def test_portfolio_parser_selects_named_monthly_block():
    fixture = """Data Library fixture

  Value Weight Returns -- Monthly
,Lo PRIOR,PRIOR 2,Hi PRIOR
201501,-1.00,2.00,3.00
201502,4.00,5.00,6.00

  Equal Weight Returns -- Monthly
,Lo PRIOR,PRIOR 2,Hi PRIOR
201501,9.00,9.00,9.00
"""
    parsed = parse_french_portfolio_block(
        fixture,
        block_title="Value Weight Returns -- Monthly",
        output_columns=("p01", "p02", "p03"),
    )
    assert list(parsed.columns) == ["date", "p01", "p02", "p03"]
    assert parsed.loc[0, "p01"] == pytest.approx(-0.01)
    assert parsed.loc[1, "p03"] == pytest.approx(0.06)


def test_momentum_validation_reports_fixed_holdout_and_monotonicity():
    dates = pd.date_range("1985-01-31", "2020-12-31", freq="ME")
    frame = pd.DataFrame({"date": dates})
    cycle = np.resize(np.array([-0.01, 0.0, 0.01]), len(frame))
    for decile in range(1, 11):
        frame[f"p{decile:02d}"] = cycle + decile * 0.001
    summary, deciles = momentum_decile_validation(frame)
    assert set(summary["period"]) == {"development", "validation", "holdout"}
    assert np.allclose(summary["mean_return_rank_correlation"], 1.0)
    assert summary["p10_minus_p01_annualized_mean"].gt(0).all()
    assert len(deciles) == 30
