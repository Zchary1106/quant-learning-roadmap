"""Explicit bridge from versioned QuantDesk bars to existing research helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from .contracts import DailyBar
from .validation import validate_daily_bars


def _single_snapshot(bars: list[DailyBar]) -> str:
    snapshot_ids = {bar.source.snapshot_id for bar in bars}
    if len(snapshot_ids) != 1:
        raise ValueError("research frame must contain exactly one snapshot_id")
    return next(iter(snapshot_ids))


def bars_to_research_frame(bars: Iterable[DailyBar]) -> pd.DataFrame:
    """Make a date-sorted research frame without dropping provenance fields."""
    records = validate_daily_bars(bars)
    if not records:
        raise ValueError("at least one daily bar is required")
    snapshot_id = _single_snapshot(records)
    frame = pd.DataFrame(
        [
            {
                "snapshot_id": snapshot_id,
                "ts_code": bar.ts_code,
                "exchange": bar.exchange.value,
                "date": pd.Timestamp(bar.trade_date),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "pre_close": bar.pre_close,
                "volume_hands": bar.volume_hands,
                "volume_shares": bar.volume_shares,
                "amount_thousand_cny": bar.amount_thousand_cny,
                "turnover_cny": bar.turnover_cny,
                "event_time": pd.Timestamp(bar.availability.event_time),
                "available_at": pd.Timestamp(bar.availability.available_at),
                "retrieved_at": pd.Timestamp(bar.availability.retrieved_at),
            }
            for bar in records
        ]
    )
    return frame.sort_values(["ts_code", "date"]).reset_index(drop=True)


def bars_to_ohlcv_frame(bars: Iterable[DailyBar]) -> pd.DataFrame:
    """Return the exact unadjusted OHLCV columns expected by ``quantlearn``.

    This function does not create an adjusted return series and does not decide
    that the bars are fillable. Callers remain responsible for the declared
    trading-time and tradability assumptions.
    """
    research = bars_to_research_frame(bars)
    return research.loc[:, ["date", "open", "high", "low", "close", "volume_shares"]].rename(
        columns={"volume_shares": "volume"}
    )
