import sqlite3

import pandas as pd
import pytest

from quantlearn.data_pipeline import (
    build_features,
    clean_ohlcv,
    quality_report,
    write_sqlite_layers,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
            "open": [10.0, 10.5, 11.0],
            "high": [10.8, 11.2, 11.5],
            "low": [9.8, 10.2, 10.7],
            "close": [10.6, 11.0, 11.2],
            "volume": [100, 120, 90],
        }
    )


def test_quality_report_detects_impossible_bar() -> None:
    frame = sample_frame()
    frame.loc[1, "low"] = 12.0
    assert quality_report(frame)["invalid_ohlc"] == 1
    with pytest.raises(ValueError):
        clean_ohlcv(frame)


def test_layers_are_queryable(tmp_path) -> None:
    raw = sample_frame()
    clean = clean_ohlcv(raw)
    features = build_features(clean)
    database = tmp_path / "market.sqlite"
    write_sqlite_layers(raw, clean, features, database)

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        clean_rows = connection.execute("SELECT COUNT(*) FROM clean_ohlcv").fetchone()[0]
    assert tables == {"raw_ohlcv", "clean_ohlcv", "features_daily"}
    assert clean_rows == 3
