"""Offline-first contracts for the QuantDesk China A-share research data layer.

The package intentionally contains no broker API or live-order capability.
"""

from .contracts import (
    DataAvailability,
    DailyBar,
    DailyBarRaw,
    Exchange,
    PointInTimeConfidence,
    SourceMetadata,
    TradeSide,
    TradabilityState,
)
from .normalize import normalize_daily_bar, raw_daily_bar_from_tushare
from .research import bars_to_ohlcv_frame, bars_to_research_frame
from .storage import read_reference_records, write_reference_records
from .tradability import assess_daily_tradability
from .universe import build_index_universe, require_verified_point_in_time
from .validation import validate_daily_bars

__all__ = [
    "DataAvailability",
    "DailyBar",
    "DailyBarRaw",
    "Exchange",
    "PointInTimeConfidence",
    "SourceMetadata",
    "TradeSide",
    "TradabilityState",
    "assess_daily_tradability",
    "bars_to_ohlcv_frame",
    "bars_to_research_frame",
    "build_index_universe",
    "normalize_daily_bar",
    "raw_daily_bar_from_tushare",
    "read_reference_records",
    "require_verified_point_in_time",
    "write_reference_records",
    "validate_daily_bars",
]
