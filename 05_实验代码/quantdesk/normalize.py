"""Explicit Tushare daily-bar parsing and provider-unit normalization."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from .contracts import (
    DataAvailability,
    DailyBar,
    DailyBarRaw,
    Exchange,
    SourceMetadata,
)

TUSHARE_DAILY_REQUIRED_FIELDS = (
    "ts_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_chg",
    "vol",
    "amount",
)


def _parse_trade_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except ValueError as error:
            raise ValueError("trade_date must use YYYYMMDD format") from error
    raise ValueError("trade_date must be a date or YYYYMMDD string")


def exchange_from_ts_code(ts_code: str) -> Exchange:
    """Resolve only the exchanges in the declared first-milestone scope."""
    code = ts_code.strip().upper()
    if code.endswith(".SH"):
        return Exchange.SSE
    if code.endswith(".SZ"):
        return Exchange.SZSE
    raise ValueError(
        f"unsupported ts_code exchange for {ts_code!r}; Phase 1 supports .SH and .SZ only"
    )


def raw_daily_bar_from_tushare(
    payload: Mapping[str, Any], source: SourceMetadata
) -> DailyBarRaw:
    """Parse one documented ``daily`` response without hiding missing fields."""
    missing = [field for field in TUSHARE_DAILY_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Tushare daily payload missing fields: {', '.join(missing)}")
    try:
        return DailyBarRaw(
            ts_code=str(payload["ts_code"]).strip().upper(),
            trade_date=_parse_trade_date(payload["trade_date"]),
            open=float(payload["open"]),
            high=float(payload["high"]),
            low=float(payload["low"]),
            close=float(payload["close"]),
            pre_close=float(payload["pre_close"]),
            change=float(payload["change"]),
            pct_chg=float(payload["pct_chg"]),
            volume_hands=float(payload["vol"]),
            amount_thousand_cny=float(payload["amount"]),
            source=source,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Tushare daily payload contains an invalid numeric value") from error


def normalize_daily_bar(raw: DailyBarRaw, availability: DataAvailability) -> DailyBar:
    """Normalize documented Tushare units while retaining original-unit columns.

    Tushare's documented ``vol`` unit is hands (100 shares) and ``amount`` is
    thousands of CNY. These transforms are deliberately visible in the result.
    """
    return DailyBar(
        ts_code=raw.ts_code,
        exchange=exchange_from_ts_code(raw.ts_code),
        trade_date=raw.trade_date,
        open=raw.open,
        high=raw.high,
        low=raw.low,
        close=raw.close,
        pre_close=raw.pre_close,
        volume_hands=raw.volume_hands,
        volume_shares=raw.volume_hands * 100.0,
        amount_thousand_cny=raw.amount_thousand_cny,
        turnover_cny=raw.amount_thousand_cny * 1_000.0,
        availability=availability,
        source=raw.source,
    )
