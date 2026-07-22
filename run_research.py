"""Run the full synthetic-data research pipeline from the repository root."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from quant_factor import (  # noqa: E402
    backtest_top_quantile,
    build_factor_panel,
    compute_factor_ic,
    compute_quantile_returns,
    generate_synthetic_panel,
    load_panel,
    performance_metrics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproducible multi-factor research")
    parser.add_argument("--input", type=Path, help="Optional point-in-time monthly CSV")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw = load_panel(args.input) if args.input else generate_synthetic_panel(seed=args.seed)
    panel = build_factor_panel(raw)
    ic = compute_factor_ic(panel)
    quantile_returns = compute_quantile_returns(panel)
    ic_values = ic.drop(columns="date")
    ic_summary = pd.DataFrame(
        {
            "mean_rank_ic": ic_values.mean(),
            "rank_ic_std": ic_values.std(ddof=1),
            "positive_ic_ratio": ic_values.apply(
                lambda series: series.dropna().gt(0).mean()
            ),
            "observations": ic_values.count(),
        }
    )
    ic_summary["icir"] = (
        ic_summary["mean_rank_ic"] / ic_summary["rank_ic_std"]
    )
    ic_summary.index.name = "factor"
    monthly = backtest_top_quantile(panel, cost_bps=args.cost_bps)
    metrics = performance_metrics(monthly["net_return"])
    metrics.update(
        {
            "average_turnover": float(monthly["turnover"].mean()),
            "total_trading_cost": float(monthly["trading_cost"].sum()),
            "data_source_is_synthetic": float(args.input is None),
        }
    )

    sensitivity_rows = []
    for cost in (0.0, 5.0, 10.0, 20.0, 50.0):
        trial = backtest_top_quantile(panel, cost_bps=cost)
        trial_metrics = performance_metrics(trial["net_return"])
        sensitivity_rows.append(
            {
                "cost_bps": cost,
                "annual_return": trial_metrics.get("annual_return"),
                "sharpe_zero_rf": trial_metrics.get("sharpe_zero_rf"),
                "max_drawdown": trial_metrics.get("max_drawdown"),
            }
        )

    csv_options = {"lineterminator": "\n"}
    monthly.to_csv(args.output_dir / "monthly_returns.csv", index=False, **csv_options)
    ic.to_csv(args.output_dir / "factor_ic.csv", index=False, **csv_options)
    ic_summary.to_csv(args.output_dir / "factor_ic_summary.csv", **csv_options)
    quantile_returns.to_csv(
        args.output_dir / "factor_quantile_returns.csv", index=False, **csv_options
    )
    quantile_returns.groupby("factor").mean(numeric_only=True).to_csv(
        args.output_dir / "factor_quantile_summary.csv", **csv_options
    )
    pd.DataFrame([metrics]).to_csv(
        args.output_dir / "metrics.csv", index=False, **csv_options
    )
    pd.DataFrame(sensitivity_rows).to_csv(
        args.output_dir / "cost_sensitivity.csv", index=False, **csv_options
    )

    input_sha256 = None
    if args.input:
        input_sha256 = hashlib.sha256(args.input.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "data": {
            "kind": "external_csv" if args.input else "deterministic_synthetic",
            "input_file": args.input.name if args.input else None,
            "input_sha256": input_sha256,
            "seed": None if args.input else args.seed,
        },
        "research_specification": {
            "frequency": "monthly",
            "factors": ["momentum_12_1", "book_to_market", "roe", "low_volatility_12m"],
            "fundamental_lag_months": 3,
            "winsorization_percentiles": [0.01, 0.99],
            "portfolio": "top_20_percent_equal_weight_long_only",
            "benchmark": "equal_weight_eligible_universe",
            "transaction_cost_bps": args.cost_bps,
            "cost_sensitivity_bps": [0, 5, 10, 20, 50],
        },
        "claim_boundary": (
            "pipeline validation only" if args.input is None else
            "user-supplied data; point-in-time validity is not established by the loader"
        ),
    }
    with (args.output_dir / "run_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    wealth = (1.0 + monthly.set_index("signal_date")["net_return"]).cumprod()
    benchmark = (1.0 + monthly.set_index("signal_date")["benchmark_return"]).cumprod()
    fig, ax = plt.subplots(figsize=(9, 5))
    wealth.plot(ax=ax, label="Multi-factor portfolio")
    benchmark.plot(ax=ax, label="Equal-weight benchmark")
    ax.set(title="Synthetic-data pipeline demonstration", ylabel="Growth of $1")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.output_dir / "equity_curve.png", dpi=160)
    plt.close(fig)

    print(pd.Series(metrics).to_string())
    print("\nSynthetic demo only; these results are not evidence of market alpha.")


if __name__ == "__main__":
    main()
