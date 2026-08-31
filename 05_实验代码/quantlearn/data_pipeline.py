"""Small, auditable OHLCV quality checks and SQLite data layers."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

OHLCV_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def load_ohlcv_csv(
    path: str | Path, column_map: Mapping[str, str] | None = None
) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if column_map:
        frame = frame.rename(columns=dict(column_map))
    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    return frame.loc[:, OHLCV_COLUMNS].copy()


def quality_report(frame: pd.DataFrame) -> dict[str, int | bool]:
    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    numeric = frame.loc[:, ("open", "high", "low", "close", "volume")].apply(
        pd.to_numeric, errors="coerce"
    )
    parsed_dates = pd.to_datetime(frame["date"], errors="coerce")
    invalid_ohlc = (
        (numeric["low"] > numeric["open"])
        | (numeric["low"] > numeric["close"])
        | (numeric["high"] < numeric["open"])
        | (numeric["high"] < numeric["close"])
        | (numeric["low"] > numeric["high"])
    )
    return {
        "rows": len(frame),
        "duplicate_dates": int(parsed_dates.duplicated().sum()),
        "missing_values": int(frame.loc[:, OHLCV_COLUMNS].isna().sum().sum()),
        "invalid_dates": int(parsed_dates.isna().sum()),
        "invalid_numeric": int(numeric.isna().sum().sum()),
        "invalid_ohlc": int(invalid_ohlc.sum()),
        "nonpositive_prices": int((numeric.loc[:, ("open", "high", "low", "close")] <= 0).sum().sum()),
        "negative_volume": int((numeric["volume"] < 0).sum()),
        "date_monotonic": bool(parsed_dates.is_monotonic_increasing),
    }


def clean_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    clean = frame.loc[:, OHLCV_COLUMNS].copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="raise")
    for column in ("open", "high", "low", "close", "volume"):
        clean[column] = pd.to_numeric(clean[column], errors="raise")
    clean = clean.sort_values("date").reset_index(drop=True)

    report = quality_report(clean)
    invalid_keys = (
        "duplicate_dates",
        "missing_values",
        "invalid_dates",
        "invalid_numeric",
        "invalid_ohlc",
        "nonpositive_prices",
        "negative_volume",
    )
    failures = {key: report[key] for key in invalid_keys if report[key]}
    if failures:
        raise ValueError(f"OHLCV quality checks failed: {failures}")
    return clean


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    clean = clean_ohlcv(frame)
    features = clean.loc[:, ("date", "close")].copy()
    features["return_1d"] = clean["close"].pct_change(fill_method=None)
    features["sma_20"] = clean["close"].rolling(20).mean()
    features["volatility_20"] = features["return_1d"].rolling(20).std() * (252**0.5)
    return features


def write_sqlite_layers(
    raw: pd.DataFrame,
    clean: pd.DataFrame,
    features: pd.DataFrame,
    database: str | Path,
) -> None:
    database_path = Path(database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        raw.to_sql("raw_ohlcv", connection, if_exists="replace", index=False)
        clean.to_sql("clean_ohlcv", connection, if_exists="replace", index=False)
        features.to_sql("features_daily", connection, if_exists="replace", index=False)
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_clean_date ON clean_ohlcv(date)"
        )
