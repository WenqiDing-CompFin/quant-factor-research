"""Download and analyze official public U.S. factor portfolio returns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from quant_factor.public_data import (  # noqa: E402
    PUBLIC_FACTOR_COLUMNS,
    load_public_factor_returns,
    load_public_momentum_portfolios,
    momentum_decile_validation,
    public_factor_subperiod_summary,
    public_factor_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate public Fama-French factor portfolio returns"
    )
    parser.add_argument("--start-date", default="1990-01-01")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data/raw/fama_french")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "results/public_factors/latest"
    )
    parser.add_argument(
        "--include-monthly",
        action="store_true",
        help="Also save full monthly source-aligned returns for local inspection",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    returns, metadata = load_public_factor_returns(args.cache_dir)
    momentum_portfolios, momentum_metadata = load_public_momentum_portfolios(
        args.cache_dir
    )
    summary = public_factor_summary(returns, start_date=args.start_date)
    subperiod = public_factor_subperiod_summary(returns)
    momentum_summary, momentum_deciles = momentum_decile_validation(
        momentum_portfolios
    )
    sample = returns.loc[returns["date"].ge(args.start_date)].copy()
    correlations = sample.loc[:, PUBLIC_FACTOR_COLUMNS].corr()
    csv_options = {"lineterminator": "\n"}
    if args.include_monthly:
        returns.to_csv(
            args.output_dir / "monthly_factor_returns.csv", index=False, **csv_options
        )
        momentum_portfolios.to_csv(
            args.output_dir / "monthly_momentum_decile_returns.csv",
            index=False,
            **csv_options,
        )
    summary.to_csv(args.output_dir / "factor_summary.csv", index=False, **csv_options)
    subperiod.to_csv(
        args.output_dir / "subperiod_summary.csv", index=False, **csv_options
    )
    correlations.to_csv(args.output_dir / "factor_correlations.csv", **csv_options)
    momentum_summary.to_csv(
        args.output_dir / "momentum_decile_summary.csv", index=False, **csv_options
    )
    momentum_deciles.to_csv(
        args.output_dir / "momentum_decile_average_returns.csv",
        index=False,
        **csv_options,
    )
    metadata["declared_evaluation_start"] = args.start_date
    metadata["momentum_decile_portfolios"] = momentum_metadata
    metadata["momentum_reporting_partitions"] = {
        "development": "1927-01 through 1989-12",
        "validation": "1990-01 through 2014-12",
        "holdout": "2015-01 through latest",
        "interpretation": (
            "Retrospective fixed partitions; not a claim of a historically "
            "untouched prospective test."
        ),
    }
    with (args.output_dir / "source_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    wealth = (1.0 + sample.set_index("date")[list(PUBLIC_FACTOR_COLUMNS)]).cumprod()
    ax = wealth.plot(figsize=(10, 6), title="Official U.S. factor portfolios")
    ax.set_ylabel("Growth of 1.0")
    ax.grid(alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output_dir / "factor_wealth.png", dpi=160)
    plt.close(ax.figure)

    momentum_sample = momentum_portfolios.set_index("date")
    momentum_spread = momentum_sample["p10"] - momentum_sample["p01"]
    momentum_wealth = (1.0 + momentum_spread).cumprod()
    ax = momentum_wealth.plot(
        figsize=(10, 5), title="Official momentum portfolios: P10 minus P1"
    )
    ax.axvline("1990-01-31", color="grey", linestyle="--", alpha=0.7)
    ax.axvline("2015-01-31", color="grey", linestyle="--", alpha=0.7)
    ax.set_yscale("log")
    ax.set_ylabel("Growth of 1.0, log scale")
    ax.grid(alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output_dir / "momentum_spread_wealth.png", dpi=160)
    plt.close(ax.figure)
    print(summary.to_string(index=False))
    print("\nOfficial momentum decile validation:")
    print(momentum_summary.to_string(index=False))
    print("\nConstructed public factor portfolios; not this project's stock strategy.")


if __name__ == "__main__":
    main()
