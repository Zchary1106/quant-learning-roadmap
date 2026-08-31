"""Lab 6: select SMA parameters inside each rolling training window."""

from pathlib import Path

from quantlearn.data_pipeline import clean_ohlcv, load_ohlcv_csv
from quantlearn.metrics import metrics_summary
from quantlearn.validation import walk_forward_sma

ROOT = Path(__file__).resolve().parents[1]
frame = load_ohlcv_csv(
    ROOT / "data" / "raw" / "aapl_2015_2017.csv",
    {
        "Date": "date",
        "AAPL.Open": "open",
        "AAPL.High": "high",
        "AAPL.Low": "low",
        "AAPL.Close": "close",
        "AAPL.Volume": "volume",
    },
)
prices = clean_ohlcv(frame)["close"].tolist()
result = walk_forward_sma(
    prices,
    parameter_grid=[(5, 20), (10, 40), (20, 60)],
    train_size=252,
    test_size=63,
    cost_bps=5.0,
)

for fold in result.folds:
    print(
        f"test={fold.test_start:>3}-{fold.test_end:<3} "
        f"params=({fold.fast:>2},{fold.slow:>2}) "
        f"train_sharpe={fold.train_sharpe:>6.2f} "
        f"test_return={fold.test_total_return:>7.2%}"
    )
print("combined OOS:", metrics_summary(result.out_of_sample_returns))
