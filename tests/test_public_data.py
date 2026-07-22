from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_factor.public_data import (  # noqa: E402
    parse_french_monthly_csv,
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
