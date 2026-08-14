"""Risk controls for portfolio construction and backtests."""

from __future__ import annotations

import numpy as np


def volatility_target_weight(
    raw_weight: float,
    realized_vol: float,
    target_vol: float = 0.10,
    max_weight: float = 0.10,
) -> float:
    """Scale a raw weight toward a portfolio volatility target.

    Parameters
    ----------
    raw_weight : float
        Equal-weight or model weight before risk scaling.
    realized_vol : float
        Trailing realized volatility for the asset.
    target_vol : float
        Annualized portfolio volatility target.
    max_weight : float
        Maximum allowed single-name weight.

    Returns
    -------
    float
        Volatility-scaled weight, capped at ``max_weight``, or zero when the
        volatility input is unusable.
    """
    if target_vol <= 0 or max_weight <= 0:
        return 0.0
    if realized_vol <= 0 or not np.isfinite(realized_vol):
        return 0.0
    scaled = raw_weight * target_vol / realized_vol
    return float(min(scaled, max_weight))


def apply_drawdown_stop(nav: np.ndarray, max_drawdown: float = 0.15) -> np.ndarray:
    """Return 1.0 while drawdown is within limit and 0.0 after a breach.

    Parameters
    ----------
    nav : np.ndarray
        Cumulative net asset values.
    max_drawdown : float
        Maximum allowed peak-to-trough drawdown, e.g. ``0.15`` for 15%.

    Returns
    -------
    np.ndarray
        Position multiplier series in ``{0.0, 1.0}``.
    """
    if not 0 < max_drawdown < 1:
        raise ValueError("max_drawdown must be between 0 and 1")
    values = np.asarray(nav, dtype=float)
    peak = np.maximum.accumulate(values)
    drawdown = values / peak - 1.0
    breached = drawdown < -max_drawdown
    # Latch the stop: once breached, stay out of the market.
    latched = np.maximum.accumulate(breached.astype(float))
    return (1.0 - latched).astype(float)
