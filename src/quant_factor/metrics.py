"""Portfolio performance metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def performance_metrics(returns: pd.Series, periods_per_year: int = 12) -> dict[str, float]:
    clean = returns.dropna().astype(float)
    if clean.empty:
        return {}
    if (clean <= -1.0).any():
        raise ValueError("Returns must be greater than -100%.")
    wealth = (1.0 + clean).cumprod()
    annual_return = wealth.iloc[-1] ** (periods_per_year / len(clean)) - 1.0
    monthly_volatility = clean.std(ddof=1)
    annual_volatility = monthly_volatility * math.sqrt(periods_per_year)
    sharpe = (
        clean.mean() / monthly_volatility * math.sqrt(periods_per_year)
        if len(clean) > 1 and monthly_volatility > 1e-12
        else float("nan")
    )
    drawdown = wealth.div(wealth.cummax().clip(lower=1.0)).sub(1.0)
    return {
        "observations": float(len(clean)),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_volatility),
        "sharpe_zero_rf": float(sharpe),
        "max_drawdown": float(drawdown.min()),
        "positive_month_ratio": float((clean > 0).mean()),
    }
