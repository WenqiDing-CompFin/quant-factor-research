"""Run the existing research pipeline with simulated or real A-share data.

This example only orchestrates data loading and output writing. The factor
construction, IC analysis, quantile diagnostics, and backtest functions are
imported from the existing package without modification.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from data.tushare_data_loader import (
    load_real_a_share_panel,
    load_simulated_panel,
)
from quant_factor import (
    backtest_top_quantile,
    build_factor_panel,
    compute_factor_ic,
    compute_quantile_returns,
    performance_metrics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run factor research with simulated or real A-share data"
    )
    parser.add_argument(
        "--data",
        choices=["simulated", "real"],
        default="simulated",
        help="Data source for the research pipeline",
    )
    parser.add_argument("--start-date", default="20230101")
    parser.add_argument("--end-date", default="20231231")
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--top-fraction", type=float, default=0.20)
    parser.add_argument("--min-stocks", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def run_simulated(args: argparse.Namespace) -> tuple[pd.DataFrame, ...]:
    raw = load_simulated_panel(seed=args.seed)
    panel = build_factor_panel(raw)
    ic = compute_factor_ic(panel)
    quantiles = compute_quantile_returns(panel)
    backtest = backtest_top_quantile(
        panel,
        top_fraction=args.top_fraction,
        cost_bps=args.cost_bps,
        min_stocks=args.min_stocks,
    )
    metrics = performance_metrics(backtest["net_return"])
    return panel, ic, quantiles, backtest, metrics


def run_real(args: argparse.Namespace) -> tuple[pd.DataFrame, ...]:
    panel = load_real_a_share_panel(
        args.start_date,
        args.end_date,
        sample_size=args.sample_size,
    )
    ic = compute_factor_ic(panel, factors=("factor_value",))
    quantiles = compute_quantile_returns(
        panel,
        factors=("factor_value",),
        quantiles=5,
    )
    backtest = backtest_top_quantile(
        panel,
        top_fraction=args.top_fraction,
        cost_bps=args.cost_bps,
        min_stocks=args.min_stocks,
    )
    metrics = performance_metrics(backtest["net_return"])
    return panel, ic, quantiles, backtest, metrics


def save_outputs(
    args: argparse.Namespace,
    ic: pd.DataFrame,
    quantiles: pd.DataFrame,
    backtest: pd.DataFrame,
    metrics: dict[str, float],
) -> Path:
    output_dir = args.output_dir or (
        ROOT / "results" / ("real_data_ashare" if args.data == "real" else "simulated")
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    ic.to_csv(output_dir / "factor_ic.csv", index=False)
    quantiles.to_csv(output_dir / "factor_quantile_returns.csv", index=False)
    backtest.to_csv(output_dir / "period_returns.csv", index=False)
    pd.DataFrame([metrics]).to_csv(output_dir / "metrics.csv", index=False)
    return output_dir


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = parse_args()

    if args.data == "real":
        panel, ic, quantiles, backtest, metrics = run_real(args)
    else:
        panel, ic, quantiles, backtest, metrics = run_simulated(args)

    output_dir = save_outputs(args, ic, quantiles, backtest, metrics)
    print(f"Data mode: {args.data}")
    print(f"Panel rows: {len(panel)}, tickers: {panel['ticker'].nunique()}")
    print("Factor IC summary:")
    print(ic.drop(columns="date").mean().round(4).to_string())
    print("Portfolio metrics:")
    print(pd.Series(metrics).round(4).to_string())
    print(f"Outputs written to: {output_dir}")

    if args.data == "real":
        print(
            "\nReal-data results depend on Tushare data availability and API "
            "quota. They are for academic research only, not investment advice. "
            "Survivorship bias remains a risk in A-share data."
        )


if __name__ == "__main__":
    main()
