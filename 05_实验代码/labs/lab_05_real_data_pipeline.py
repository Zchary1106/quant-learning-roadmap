"""Lab 5: validate a fixed real-data snapshot and create SQLite layers."""

from pathlib import Path

from quantlearn.data_pipeline import (
    build_features,
    clean_ohlcv,
    load_ohlcv_csv,
    quality_report,
    write_sqlite_layers,
)

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "data" / "raw" / "aapl_2015_2017.csv"
database = ROOT / "data" / "processed" / "market.sqlite"

raw = load_ohlcv_csv(
    source,
    {
        "Date": "date",
        "AAPL.Open": "open",
        "AAPL.High": "high",
        "AAPL.Low": "low",
        "AAPL.Close": "close",
        "AAPL.Volume": "volume",
    },
)
print("raw quality:", quality_report(raw))

clean = clean_ohlcv(raw)
features = build_features(clean)
write_sqlite_layers(raw, clean, features, database)

print(f"wrote {len(clean)} rows to {database}")
display = features.tail(3).copy()
numeric_columns = display.select_dtypes(include="number").columns
display.loc[:, numeric_columns] = display.loc[:, numeric_columns].round(4)
print(display.to_string(index=False))
