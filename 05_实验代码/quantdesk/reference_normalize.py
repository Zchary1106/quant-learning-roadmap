"""Explicit parsing for non-daily-bar Tushare records declared in design v3.1."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from .contracts import (
    AdjustmentFactor,
    DailyBasicRecord,
    DataAvailability,
    DividendEvent,
    Exchange,
    IndexMembership,
    LimitBand,
    ListingStatus,
    PointInTimeConfidence,
    SecurityMasterRecord,
    SourceMetadata,
    StStatus,
    SuspensionEvent,
    TradingSession,
)
from .normalize import _parse_trade_date, exchange_from_ts_code


def _required(payload: Mapping[str, Any], field: str) -> Any:
    if field not in payload or payload[field] in (None, ""):
        raise ValueError(f"payload missing required field: {field}")
    return payload[field]


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    return _parse_trade_date(value)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"expected numeric value, got {value!r}") from error


def _parse_exchange(value: Any) -> Exchange:
    normalized = str(value).strip().upper()
    aliases = {
        "SSE": Exchange.SSE,
        "SH": Exchange.SSE,
        "SZSE": Exchange.SZSE,
        "SZ": Exchange.SZSE,
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(f"unsupported exchange in Phase 1 scope: {value!r}") from error


def _parse_yes_no(value: Any, field: str) -> bool:
    normalized = str(_required({"value": value}, "value")).strip().upper()
    if normalized == "Y":
        return True
    if normalized == "N":
        return False
    raise ValueError(f"{field} must be Y or N")


def normalize_security_master(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    point_in_time_confidence: PointInTimeConfidence = PointInTimeConfidence.UNKNOWN,
) -> SecurityMasterRecord:
    ts_code = str(_required(payload, "ts_code")).strip().upper()
    listing_status = str(_required(payload, "list_status")).strip().upper()
    try:
        status = ListingStatus(listing_status)
    except ValueError as error:
        raise ValueError(f"unsupported list_status: {listing_status!r}") from error
    exchange = _parse_exchange(payload.get("exchange", exchange_from_ts_code(ts_code).value))
    if exchange is not exchange_from_ts_code(ts_code):
        raise ValueError("exchange field does not match ts_code suffix")
    return SecurityMasterRecord(
        ts_code=ts_code,
        symbol=str(_required(payload, "symbol")).strip(),
        name=str(_required(payload, "name")).strip(),
        exchange=exchange,
        listing_status=status,
        list_date=_parse_trade_date(_required(payload, "list_date")),
        delist_date=_optional_date(payload.get("delist_date")),
        point_in_time_confidence=point_in_time_confidence,
        source=source,
    )


def normalize_trading_session(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
) -> TradingSession:
    open_flag = str(_required(payload, "is_open")).strip()
    if open_flag not in {"0", "1"}:
        raise ValueError("is_open must be 0 or 1")
    return TradingSession(
        exchange=_parse_exchange(_required(payload, "exchange")),
        session_date=_parse_trade_date(_required(payload, "cal_date")),
        is_open=open_flag == "1",
        previous_open_date=_optional_date(payload.get("pretrade_date")),
        availability=availability,
        source=source,
    )


def normalize_adjustment_factor(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
) -> AdjustmentFactor:
    return AdjustmentFactor(
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        trade_date=_parse_trade_date(_required(payload, "trade_date")),
        factor=float(_required(payload, "adj_factor")),
        availability=availability,
        source=source,
    )


def normalize_dividend_event(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
) -> DividendEvent:
    return DividendEvent(
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        end_date=_optional_date(payload.get("end_date")),
        announcement_date=_optional_date(payload.get("ann_date")),
        implementation_announcement_date=_optional_date(payload.get("imp_ann_date")),
        process_status=str(payload.get("div_proc") or "").strip(),
        stock_dividend_per_share=_optional_float(payload.get("stk_div")),
        cash_dividend_after_tax_per_share=_optional_float(payload.get("cash_div")),
        cash_dividend_pre_tax_per_share=_optional_float(payload.get("cash_div_tax")),
        record_date=_optional_date(payload.get("record_date")),
        ex_date=_optional_date(payload.get("ex_date")),
        pay_date=_optional_date(payload.get("pay_date")),
        stock_list_date=_optional_date(payload.get("div_listdate")),
        availability=availability,
        source=source,
    )


def normalize_limit_band(payload: Mapping[str, Any], *, source: SourceMetadata) -> LimitBand:
    return LimitBand(
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        trade_date=_parse_trade_date(_required(payload, "trade_date")),
        up_limit=float(_required(payload, "up_limit")),
        down_limit=float(_required(payload, "down_limit")),
        source=source,
    )


def normalize_suspension_event(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
) -> SuspensionEvent:
    timing_code = str(_required(payload, "suspend_timing")).strip().upper()
    if timing_code not in {"S", "R"}:
        raise ValueError("suspend_timing must be S or R")
    return SuspensionEvent(
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        trade_date=_parse_trade_date(_required(payload, "trade_date")),
        timing_code=timing_code,
        suspension_type=(str(payload["suspend_type"]).strip() if payload.get("suspend_type") else None),
        availability=availability,
        source=source,
    )


def normalize_st_status(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
    type_mapping: Mapping[str, bool],
) -> StStatus:
    type_code = str(_required(payload, "type")).strip().upper()
    if type_code not in type_mapping:
        raise ValueError(f"unrecognized stock_st type code: {type_code!r}")
    type_name = str(_required(payload, "type_name")).strip()
    return StStatus(
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        name=str(_required(payload, "name")).strip(),
        trade_date=_parse_trade_date(_required(payload, "trade_date")),
        is_st=bool(type_mapping[type_code]),
        type_code=type_code,
        label=type_name,
        availability=availability,
        source=source,
    )


def normalize_daily_basic(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
) -> DailyBasicRecord:
    return DailyBasicRecord(
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        trade_date=_parse_trade_date(_required(payload, "trade_date")),
        close=_optional_float(payload.get("close")),
        total_share_ten_thousand=_optional_float(payload.get("total_share")),
        float_share_ten_thousand=_optional_float(payload.get("float_share")),
        free_share_raw=_optional_float(payload.get("free_share")),
        total_market_value_ten_thousand_cny=_optional_float(payload.get("total_mv")),
        circulating_market_value_ten_thousand_cny=_optional_float(payload.get("circ_mv")),
        availability=availability,
        source=source,
    )


def normalize_index_membership(
    payload: Mapping[str, Any],
    *,
    source: SourceMetadata,
    availability: DataAvailability,
    point_in_time_confidence: PointInTimeConfidence = PointInTimeConfidence.EFFECTIVE_INTERVAL_ONLY,
) -> IndexMembership:
    return IndexMembership(
        index_code=str(_required(payload, "l3_code")).strip().upper(),
        ts_code=str(_required(payload, "ts_code")).strip().upper(),
        in_date=_parse_trade_date(_required(payload, "in_date")),
        out_date=_optional_date(payload.get("out_date")),
        is_current_membership_flag=_parse_yes_no(payload.get("is_new"), "is_new"),
        availability=availability,
        point_in_time_confidence=point_in_time_confidence,
        source=source,
    )
