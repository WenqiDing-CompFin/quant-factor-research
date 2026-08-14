"""Portfolio performance metrics."""

from __future__ import annotations

import math

import pandas as pd


def performance_metrics(
    returns: pd.Series,
    periods_per_year: int = 12,
    benchmark_returns: pd.Series | None = None,
) -> dict[str, float]:
    """Compute core performance and risk metrics from a return series.

    Parameters
    ----------
    returns : pd.Series
        Portfolio returns, already adjusted for costs.
    periods_per_year : int
        Number of return periods per year, 12 for monthly data.
    benchmark_returns : pd.Series, optional
        Benchmark returns used for the information ratio.

    Returns
    -------
    dict[str, float]
        Observation count, return, volatility, Sharpe, Sortino, Calmar,
        information ratio, drawdown, and positive-month ratio.
    """
    clean = returns.dropna().astype(float)
    if clean.empty:
        return {}
    if (clean <= -1.0).any():
        raise ValueError("Returns must be greater than -100%.")
    wealth = (1.0 + clean).cumprod()
    annual_return = wealth.iloc[-1] ** (periods_per_year / len(clean)) - 1.0
    monthly_volatility = clean.std(ddof=1) if len(clean) > 1 else float("nan")
    annual_volatility = (
        monthly_volatility * math.sqrt(periods_per_year)
        if math.isfinite(monthly_volatility)
        else float("nan")
    )
    sharpe = (
        clean.mean() / monthly_volatility * math.sqrt(periods_per_year)
        if len(clean) > 1 and monthly_volatility > 1e-12
        else float("nan")
    )
    drawdown = wealth.div(wealth.cummax().clip(lower=1.0)).sub(1.0)
    downside = clean.loc[clean < 0.0]
    downside_volatility = (
        downside.std(ddof=1)
        if len(downside) > 1 and downside.std(ddof=1) > 1e-12
        else float("nan")
    )
    sortino = (
        clean.mean() / downside_volatility * math.sqrt(periods_per_year)
        if math.isfinite(downside_volatility)
        else float("nan")
    )
    max_drawdown = float(drawdown.min())
    calmar = (
        annual_return / abs(max_drawdown) if abs(max_drawdown) > 1e-12 else float("nan")
    )

    information_ratio = float("nan")
    if benchmark_returns is not None:
        benchmark = benchmark_returns.reindex(clean.index).dropna()
        if not benchmark.empty:
            aligned = clean.loc[benchmark.index]
            excess = aligned - benchmark
            tracking_error = excess.std(ddof=1)
            if (
                len(excess) > 1
                and math.isfinite(tracking_error)
                and tracking_error > 1e-12
            ):
                information_ratio = (
                    excess.mean() / tracking_error * math.sqrt(periods_per_year)
                )

    return {
        "observations": float(len(clean)),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_volatility),
        "sharpe_zero_rf": float(sharpe),
        "sortino_zero_rf": float(sortino),
        "calmar_ratio": float(calmar),
        "information_ratio": float(information_ratio),
        "max_drawdown": max_drawdown,
        "positive_month_ratio": float((clean > 0).mean()),
    }
