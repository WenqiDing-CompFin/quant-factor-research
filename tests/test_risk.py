import numpy as np
import pytest

from quant_factor.risk import apply_drawdown_stop, volatility_target_weight


def test_volatility_target_scales_weight():
    assert (
        pytest.approx(
            volatility_target_weight(raw_weight=0.1, realized_vol=0.2, target_vol=0.1)
        )
        == 0.05
    )


def test_volatility_target_respects_max_weight():
    assert (
        volatility_target_weight(
            raw_weight=0.1, realized_vol=0.05, target_vol=0.1, max_weight=0.04
        )
        == 0.04
    )


def test_volatility_target_returns_zero_for_invalid_vol():
    assert volatility_target_weight(0.1, float("nan")) == 0.0
    assert volatility_target_weight(0.1, -1.0) == 0.0


def test_drawdown_stop_turns_off_after_breach():
    nav = np.array([1.0, 1.1, 0.9, 0.95])
    result = apply_drawdown_stop(nav, max_drawdown=0.15)
    assert result.tolist() == [1.0, 1.0, 0.0, 0.0]
