"""Reproducible educational multi-factor research package."""

from .backtest import backtest_top_quantile
from .data import generate_synthetic_panel, load_panel, validate_panel
from .factors import build_factor_panel, compute_factor_ic, compute_quantile_returns
from .metrics import performance_metrics
from .public_data import (
    load_public_factor_returns,
    public_factor_subperiod_summary,
    public_factor_summary,
)

__all__ = [
    "backtest_top_quantile",
    "build_factor_panel",
    "compute_factor_ic",
    "compute_quantile_returns",
    "generate_synthetic_panel",
    "load_panel",
    "performance_metrics",
    "load_public_factor_returns",
    "public_factor_subperiod_summary",
    "public_factor_summary",
    "validate_panel",
]
