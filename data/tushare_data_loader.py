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
) -> pd.DataFrame:
    """Convert one ticker's qfq bars into the standard research panel."""
    if bars is None or bars.empty:
        return pd.DataFrame()

    frame = bars.copy()
    frame = frame.rename(columns={"trade_date": "date", "ts_code": "asset_id"})
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d", errors="coerce")
    frame["asset_id"] = frame["asset_id"].astype(str)
    frame["ticker"] = frame["asset_id"]
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["date", "close"])
    frame = frame.loc[frame["close"] > 0]

    if "vol" in frame.columns:
        frame["vol"] = pd.to_numeric(frame["vol"], errors="coerce").fillna(0.0)
        frame = frame.loc[frame["vol"] > 0]

    frame = frame.sort_values(["asset_id", "date"]).reset_index(drop=True)
    grouped = frame.groupby("asset_id", sort=False)["close"]
    frame["factor_value"] = grouped.pct_change(MOMENTUM_WINDOW)
    frame["return"] = grouped.shift(-1).div(frame["close"]).sub(1)
    frame["future_return_1m"] = frame["return"]
    frame["composite_score"] = frame["factor_value"]
    return frame.dropna(subset=["factor_value", "return"])


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
            ticker_frame = _build_ticker_panel(bars, code)
            if not ticker_frame.empty:
                frames.append(ticker_frame)
        except Exception:
            logger.exception("Skipping ticker %s after repeated failures", code)

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
    panel = (
        panel.dropna(subset=["factor_value", "return"])
        .sort_values(["date", "asset_id"])
        .reset_index(drop=True)
    )
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
