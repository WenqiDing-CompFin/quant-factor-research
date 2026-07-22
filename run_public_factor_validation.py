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
        "--output-dir", type=Path, default=ROOT / "results/public_factors/generated"
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    returns, metadata = load_public_factor_returns(args.cache_dir)
    summary = public_factor_summary(returns, start_date=args.start_date)
    subperiod = public_factor_subperiod_summary(returns)
    sample = returns.loc[returns["date"].ge(args.start_date)].copy()
    correlations = sample.loc[:, PUBLIC_FACTOR_COLUMNS].corr()
    csv_options = {"lineterminator": "\n"}
    returns.to_csv(
        args.output_dir / "monthly_factor_returns.csv", index=False, **csv_options
    )
    summary.to_csv(args.output_dir / "factor_summary.csv", index=False, **csv_options)
    subperiod.to_csv(
        args.output_dir / "subperiod_summary.csv", index=False, **csv_options
    )
    correlations.to_csv(args.output_dir / "factor_correlations.csv", **csv_options)
    metadata["declared_evaluation_start"] = args.start_date
    with (args.output_dir / "source_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    wealth = (1.0 + sample.set_index("date")[list(PUBLIC_FACTOR_COLUMNS)]).cumprod()
    ax = wealth.plot(figsize=(10, 6), title="Official U.S. factor portfolios")
    ax.set_ylabel("Growth of 1.0")
    ax.grid(alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output_dir / "factor_wealth.png", dpi=160)
    plt.close(ax.figure)
    print(summary.to_string(index=False))
    print("\nConstructed public factor portfolios; not this project's stock strategy.")


if __name__ == "__main__":
    main()
