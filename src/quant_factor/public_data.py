"""Official public factor-return data and dependence-aware diagnostics."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


OFFICIAL_SOURCE_PAGE = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
)
FIVE_FACTOR_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)
MOMENTUM_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Momentum_Factor_CSV.zip"
)
PUBLIC_FACTOR_COLUMNS = (
    "market_excess",
    "size",
    "value",
    "profitability",
    "investment",
    "momentum",
)


def parse_french_monthly_csv(
    text: str, expected_columns: tuple[str, ...]
) -> pd.DataFrame:
    """Parse the first monthly block in a Kenneth French Data Library CSV."""
    rows = list(csv.reader(io.StringIO(text)))
    header_index = None
    header: list[str] = []
    for index, row in enumerate(rows):
        normalized = [value.strip() for value in row]
        if set(expected_columns).issubset(normalized):
            header_index = index
            header = normalized
            break
    if header_index is None:
        raise ValueError(f"Could not find monthly header: {expected_columns}")

    records: list[dict[str, object]] = []
    for row in rows[header_index + 1 :]:
        if not row:
            break
        month = row[0].strip()
        if not re.fullmatch(r"\d{6}", month):
            break
        if len(row) < len(header):
            raise ValueError(f"Incomplete monthly row for {month}")
        record: dict[str, object] = {
            "date": pd.Period(month, freq="M").to_timestamp("M")
        }
        for position, column in enumerate(header[1:], start=1):
            if not column:
                continue
            value = float(row[position].strip())
            record[column] = np.nan if value <= -99.0 else value / 100.0
        records.append(record)
    if not records:
        raise ValueError("No monthly observations found in public factor CSV")
    return pd.DataFrame.from_records(records).sort_values("date").reset_index(drop=True)


def _read_archive(
    url: str, cache_dir: Path, timeout_seconds: int = 30
) -> tuple[str, dict[str, object]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = cache_dir / url.rsplit("/", 1)[-1]
    if archive_path.exists():
        payload = archive_path.read_bytes()
    else:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "quant-factor-research/0.1 public-data validation"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read()
        archive_path.write_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise ValueError(f"Expected one CSV in {archive_path.name}, found {csv_members}")
        member = csv_members[0]
        text = archive.read(member).decode("cp1252")
    metadata = {
        "url": url,
        "cache_file": archive_path.name,
        "archive_member": member,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    return text, metadata


def load_public_factor_returns(
    cache_dir: str | Path = "data/raw/fama_french",
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Download and align official monthly five-factor and momentum returns.

    Returns are decimal monthly returns. The files contain constructed factor
    portfolios, not security-level observations or evidence for this repository's
    synthetic stock-selection strategy.
    """
    destination = Path(cache_dir)
    five_text, five_metadata = _read_archive(FIVE_FACTOR_URL, destination)
    momentum_text, momentum_metadata = _read_archive(MOMENTUM_URL, destination)
    five = parse_french_monthly_csv(
        five_text, ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
    )
    momentum = parse_french_monthly_csv(momentum_text, ("Mom",))
    merged = five.merge(momentum, on="date", how="inner", validate="one_to_one")
    merged = merged.rename(
        columns={
            "Mkt-RF": "market_excess",
            "SMB": "size",
            "HML": "value",
            "RMW": "profitability",
            "CMA": "investment",
            "RF": "risk_free",
            "Mom": "momentum",
        }
    )
    metadata = {
        "source_page": OFFICIAL_SOURCE_PAGE,
        "return_unit": "decimal monthly return",
        "five_factor_archive": five_metadata,
        "momentum_archive": momentum_metadata,
        "combined_start": str(merged["date"].min().date()),
        "combined_end": str(merged["date"].max().date()),
        "observations": len(merged),
        "claim_boundary": (
            "Official constructed factor portfolios; not a security-level backtest "
            "of this repository's composite strategy."
        ),
    }
    return merged, metadata


def newey_west_mean_tstat(returns: pd.Series, lags: int = 6) -> float:
    """Return the Newey-West t-statistic for a monthly mean."""
    values = returns.dropna().to_numpy(dtype=float)
    if lags < 0:
        raise ValueError("lags cannot be negative")
    if len(values) < 3:
        return float("nan")
    residuals = values - values.mean()
    long_run_variance = float(residuals @ residuals / len(values))
    usable_lags = min(lags, len(values) - 1)
    for lag in range(1, usable_lags + 1):
        weight = 1.0 - lag / (usable_lags + 1.0)
        covariance = float(residuals[lag:] @ residuals[:-lag] / len(values))
        long_run_variance += 2.0 * weight * covariance
    if long_run_variance <= 0:
        return float("nan")
    standard_error = math.sqrt(long_run_variance / len(values))
    return float(values.mean() / standard_error)


def public_factor_summary(
    factor_returns: pd.DataFrame,
    start_date: str = "1990-01-01",
    newey_west_lags: int = 6,
) -> pd.DataFrame:
    """Summarize real factor portfolios over a declared evaluation window."""
    sample = factor_returns.loc[
        pd.to_datetime(factor_returns["date"]) >= pd.Timestamp(start_date)
    ].copy()
    if sample.empty:
        raise ValueError("No public factor observations remain after start_date")
    rows = []
    for factor in PUBLIC_FACTOR_COLUMNS:
        values = sample[factor].dropna().astype(float)
        wealth = (1.0 + values).cumprod()
        drawdown = wealth.div(wealth.cummax().clip(lower=1.0)).sub(1.0)
        monthly_volatility = values.std(ddof=1)
        rows.append(
            {
                "factor": factor,
                "start_date": str(sample.loc[values.index, "date"].min().date()),
                "end_date": str(sample.loc[values.index, "date"].max().date()),
                "observations": len(values),
                "annualized_mean": float(values.mean() * 12.0),
                "annualized_volatility": float(monthly_volatility * math.sqrt(12.0)),
                "sharpe_zero_rf": float(
                    values.mean() / monthly_volatility * math.sqrt(12.0)
                ) if monthly_volatility > 1e-12 else float("nan"),
                "max_drawdown": float(drawdown.min()),
                "positive_month_ratio": float(values.gt(0).mean()),
                "newey_west_mean_tstat": newey_west_mean_tstat(
                    values, lags=newey_west_lags
                ),
            }
        )
    return pd.DataFrame(rows)


def public_factor_subperiod_summary(factor_returns: pd.DataFrame) -> pd.DataFrame:
    """Report fixed regimes without selecting dates from observed performance."""
    periods = (
        ("1990-2006", "1990-01-01", "2006-12-31"),
        ("2007-2019", "2007-01-01", "2019-12-31"),
        ("2020-latest", "2020-01-01", None),
    )
    rows = []
    dates = pd.to_datetime(factor_returns["date"])
    for label, start, end in periods:
        mask = dates.ge(pd.Timestamp(start))
        if end:
            mask &= dates.le(pd.Timestamp(end))
        period_data = factor_returns.loc[mask]
        if period_data.empty:
            continue
        summary = public_factor_summary(period_data, start_date=start)
        summary.insert(0, "period", label)
        rows.append(summary)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
