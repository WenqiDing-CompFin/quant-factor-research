"""Tushare Pro adapter for real China A-share data.

This module is a data-layer-only adapter. It does not modify factor
construction, IC diagnostics, quantile analysis, or the backtest engine.
The simulated panel remains the default fallback.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 0.35
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.0
DEFAULT_SAMPLE_SEED = 42
MOMENTUM_WINDOW = 20


def _format_date(value: str | pd.Timestamp) -> str:
    """Normalize a date input to Tushare's YYYYMMDD string format."""
    return pd.Timestamp(value).strftime("%Y%m%d")


def _require_token() -> str:
    """Read the Tushare token from the environment."""
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("Environment variable TUSHARE_TOKEN is not set.")
    return token.strip()


def _call_with_retry(
    func: Callable[..., pd.DataFrame | None],
    retries: int = MAX_RETRIES,
    **kwargs,
) -> pd.DataFrame | None:
    """Call a Tushare function with rate limiting and bounded retries."""
    for attempt in range(1, retries + 1):
        try:
            result = func(**kwargs)
            time.sleep(RATE_LIMIT_SECONDS)
            return result
        except Exception as exc:
            logger.warning(
                "Tushare call failed (attempt %d/%d): %s",
                attempt,
                retries,
                exc,
            )
            if attempt == retries:
                raise
            time.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))
    return None


def _load_universe(
    pro: object,
    sample_size: int | None,
) -> list[str]:
    """Load currently listed A-share codes and filter obvious ST names."""
    basic = _call_with_retry(
        pro.stock_basic,
        exchange="",
        list_status="L",
        fields="ts_code,name",
    )
    if basic is None or basic.empty:
        raise RuntimeError("Tushare stock_basic returned no rows.")

    basic = basic.copy()
    basic["name"] = basic["name"].fillna("")
    basic = basic.loc[
        ~basic["name"].str.contains("ST|退", case=False, regex=True, na=False)
    ]
    codes = sorted(basic["ts_code"].astype(str).tolist())
    if not codes:
        raise RuntimeError("No tradeable A-share codes remain after filtering.")

    if sample_size:
        rng = np.random.default_rng(DEFAULT_SAMPLE_SEED)
        codes = sorted(
            rng.choice(
                codes,
                size=min(sample_size, len(codes)),
                replace=False,
            ).tolist()
        )
    return codes


def _build_ticker_panel(
    bars: pd.DataFrame | None,
    asset_id: str,
    trading_dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Align daily bars to trading sessions without filling missing prices."""
    if bars is None or bars.empty:
        raise ValueError(f"No bars returned for {asset_id}; cause is unknown")

    frame = bars.copy()
    frame = frame.rename(columns={"trade_date": "date", "ts_code": "asset_id"})
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d", errors="coerce")
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise ValueError(f"Invalid or duplicate bar dates for {asset_id}")
    if not frame["asset_id"].eq(asset_id).all():
        raise ValueError(f"Bar identity mismatch for {asset_id}")
    if not frame["date"].isin(trading_dates).all():
        raise ValueError(f"Bar dates outside trading calendar for {asset_id}")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame.loc[~np.isfinite(frame["close"]) | (frame["close"] <= 0), "close"] = np.nan

    if "vol" in frame.columns:
        volume = pd.to_numeric(frame["vol"], errors="coerce")
        frame.loc[~np.isfinite(volume) | (volume <= 0), "close"] = np.nan

    frame = (
        frame.set_index("date").reindex(trading_dates).rename_axis("date").reset_index()
    )
    frame["asset_id"] = asset_id
    frame["ticker"] = asset_id
    close = frame["close"]
    frame["factor_value"] = close.pct_change(MOMENTUM_WINDOW, fill_method=None)
    frame["return"] = close.shift(-1).div(close).sub(1)
    frame["future_return_1m"] = frame["return"]
    frame["composite_score"] = frame["factor_value"]
    return frame


def _load_trading_dates(pro: object, start: str, end: str) -> pd.DatetimeIndex:
    """Require a complete daily calendar, including closed days, before alignment."""
    calendar = _call_with_retry(
        pro.trade_cal, exchange="SSE", start_date=start, end_date=end
    )
    if (
        calendar is None
        or calendar.empty
        or not {"cal_date", "is_open"}.issubset(calendar.columns)
    ):
        raise ValueError("Tushare trading calendar is missing or incomplete")
    dates = pd.to_datetime(calendar["cal_date"], format="%Y%m%d", errors="coerce")
    flags = pd.to_numeric(calendar["is_open"], errors="coerce")
    expected = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="D")
    if dates.isna().any() or dates.duplicated().any() or not flags.isin([0, 1]).all():
        raise ValueError("Tushare trading calendar has invalid dates or open flags")
    if set(dates) != set(expected):
        raise ValueError(
            "Tushare trading calendar does not cover every requested calendar day"
        )
    trading_dates = pd.DatetimeIndex(dates[flags.eq(1)]).sort_values()
    if len(trading_dates) < 2:
        raise ValueError("At least two trading sessions are required")
    return trading_dates


def load_real_a_share_panel(
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp,
    sample_size: int | None = None,
) -> pd.DataFrame:
    """Load a real A-share panel through Tushare Pro.

    The returned panel keeps ``date`` and ``asset_id`` as columns so the
    existing IC and backtest functions can consume it directly. It also
    contains ``ticker``, ``close``, ``factor_value``, ``return``,
    ``future_return_1m``, and ``composite_score``.
    """
    token = _require_token()
    try:
        import tushare as ts
    except ImportError as exc:
        raise RuntimeError(
            "tushare is not installed. Run `pip install tushare`."
        ) from exc

    start = _format_date(start_date)
    end = _format_date(end_date)
    if start > end:
        raise ValueError("start_date must be before end_date.")

    ts.set_token(token)
    pro = ts.pro_api(token)
    codes = _load_universe(pro, sample_size)
    trading_dates = _load_trading_dates(pro, start, end)
    logger.info("Loading %d A-share tickers from %s to %s", len(codes), start, end)

    frames: list[pd.DataFrame] = []
    for code in codes:
        try:
            bars = _call_with_retry(
                ts.pro_bar,
                ts_code=code,
                adj="qfq",
                start_date=start,
                end_date=end,
            )
            ticker_frame = _build_ticker_panel(bars, code, trading_dates)
            if not ticker_frame.empty:
                frames.append(ticker_frame)
        except Exception as exc:
            raise RuntimeError(f"Failed to load or validate ticker {code}") from exc

    if not frames:
        raise RuntimeError(
            "No A-share panel could be loaded. Check the token, API points, "
            "and date range."
        )

    panel = pd.concat(frames, ignore_index=True)
    panel = panel[
        [
            "date",
            "asset_id",
            "ticker",
            "close",
            "factor_value",
            "return",
            "future_return_1m",
            "composite_score",
        ]
    ]
    panel = panel.sort_values(["date", "asset_id"]).reset_index(drop=True)
    logger.info(
        "Loaded real A-share panel with %d rows and %d tickers",
        len(panel),
        panel["asset_id"].nunique(),
    )
    return panel


def load_simulated_panel(seed: int = 7) -> pd.DataFrame:
    """Load the original deterministic simulated panel as a fallback."""
    from quant_factor import generate_synthetic_panel

    return generate_synthetic_panel(seed=seed)
