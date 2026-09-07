"""Lab 9: run the complete offline QuantDesk research-data path.

This lab uses synthetic provider-shaped data. It does not call Tushare, does
not need a token, and cannot submit an order.
"""

from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from quantdesk.contracts import DataAvailability, SourceMetadata
from quantdesk.normalize import normalize_daily_bar, raw_daily_bar_from_tushare
from quantdesk.research import bars_to_ohlcv_frame, bars_to_research_frame
from quantdesk.storage import read_daily_bars, write_daily_bars, write_raw_snapshot
from quantlearn.backtest import run_sma_backtest
from quantlearn.metrics import metrics_summary


ROOT = Path(__file__).resolve().parents[1]
SHANGHAI = ZoneInfo("Asia/Shanghai")
SOURCE = SourceMetadata(
    provider="fixture",
    endpoint="daily",
    source_url="local://lab_09_quantdesk_research_store",
    retrieved_at=datetime(2026, 9, 5, 8, 0, tzinfo=SHANGHAI),
    snapshot_id="lab-09-synthetic-20260905",
)
RAW_ROOT = ROOT / "data" / "quantdesk" / "raw"
DATABASE = ROOT / "data" / "quantdesk" / "research" / "lab_09.sqlite"


def business_days(start: date, count: int) -> list[date]:
    days: list[date] = []
    candidate = start
    while len(days) < count:
        if candidate.weekday() < 5:
            days.append(candidate)
        candidate += timedelta(days=1)
    return days


payloads = []
previous_close = 10.0
for index, trade_day in enumerate(business_days(date(2026, 8, 3), 24)):
    close = round(10.0 + index * 0.08 + (0.16 if index % 5 == 0 else -0.04), 2)
    payloads.append(
        {
            "ts_code": "600000.SH",
            "trade_date": trade_day.strftime("%Y%m%d"),
            "open": round(previous_close + 0.01, 2),
            "high": round(max(previous_close, close) + 0.12, 2),
            "low": round(min(previous_close, close) - 0.10, 2),
            "close": close,
            "pre_close": previous_close,
            "change": round(close - previous_close, 2),
            "pct_chg": round((close / previous_close - 1.0) * 100, 4),
            "vol": 10_000 + index * 25,
            "amount": 10_000 + index * 120,
        }
    )
    previous_close = close

manifest = write_raw_snapshot(
    payloads,
    source=SOURCE,
    parameters={"ts_code": "600000.SH", "source": "synthetic_lab"},
    fields=tuple(payloads[0]),
    row_count=len(payloads),
    raw_root=RAW_ROOT,
)
bars = []
for payload in payloads:
    trade_day = datetime.strptime(payload["trade_date"], "%Y%m%d").date()
    availability = DataAvailability(
        event_time=datetime.combine(trade_day, time(15, 0), SHANGHAI),
        available_at=datetime.combine(trade_day, time(16, 0), SHANGHAI),
        retrieved_at=SOURCE.retrieved_at,
    )
    bars.append(normalize_daily_bar(raw_daily_bar_from_tushare(payload, SOURCE), availability))

write_daily_bars(bars, DATABASE)
stored = read_daily_bars(
    DATABASE, snapshot_id=SOURCE.snapshot_id, ts_code="600000.SH"
)
research = bars_to_research_frame(stored)
ohlcv = bars_to_ohlcv_frame(stored)
backtest = run_sma_backtest(ohlcv["close"].tolist(), fast=3, slow=6, cost_bps=5.0)

print(f"snapshot={manifest.snapshot_id} sha256={manifest.sha256[:12]} rows={manifest.row_count}")
print(f"research rows={len(research)} available_at_max={research['available_at'].max().isoformat()}")
print("strategy metrics:", metrics_summary(backtest["strategy_returns"]))
print("boundary: synthetic data only; no provider call, no tradability fill model, no real orders.")
