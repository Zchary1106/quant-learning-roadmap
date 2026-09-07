"""Canonical, provider-neutral contracts for daily China A-share research data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class Exchange(str, Enum):
    """Exchanges supported by the first QuantDesk research milestone."""

    SSE = "SSE"
    SZSE = "SZSE"


class ListingStatus(str, Enum):
    """Provider listing-status codes retained without implying daily tradability."""

    LISTED = "L"
    DELISTED = "D"
    PAUSED_LISTING = "P"


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PointInTimeConfidence(str, Enum):
    """How strongly a historical record can support point-in-time research."""

    VERIFIED = "VERIFIED"
    EFFECTIVE_INTERVAL_ONLY = "EFFECTIVE_INTERVAL_ONLY"
    UNKNOWN = "UNKNOWN"


class TradabilityState(str, Enum):
    """Conservative three-valued result used when daily data cannot prove fills."""

    TRADEABLE = "TRADEABLE"
    NOT_TRADEABLE = "NOT_TRADEABLE"
    UNKNOWN = "UNKNOWN"


class TradabilityReason(str, Enum):
    MARKET_CLOSED = "MARKET_CLOSED"
    MISSING_TRADING_SESSION = "MISSING_TRADING_SESSION"
    SUSPENDED = "SUSPENDED"
    MISSING_BAR = "MISSING_BAR"
    MISSING_LIMIT_BAND = "MISSING_LIMIT_BAND"
    MISSING_SUSPENSION_STATUS = "MISSING_SUSPENSION_STATUS"
    AT_UPPER_LIMIT = "AT_UPPER_LIMIT"
    AT_LOWER_LIMIT = "AT_LOWER_LIMIT"


def _require_timezone(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True)
class SourceMetadata:
    """Traceability information attached to every imported provider record."""

    provider: str
    endpoint: str
    source_url: str
    retrieved_at: datetime
    snapshot_id: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.provider.strip(),
                self.endpoint.strip(),
                self.source_url.strip(),
                self.snapshot_id.strip(),
            )
        ):
            raise ValueError("source metadata fields must not be empty")
        _require_timezone(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True)
class DataAvailability:
    """When a data event occurred, became usable, and was acquired by this system."""

    event_time: datetime
    available_at: datetime
    retrieved_at: datetime

    def __post_init__(self) -> None:
        _require_timezone(self.event_time, "event_time")
        _require_timezone(self.available_at, "available_at")
        _require_timezone(self.retrieved_at, "retrieved_at")
        if self.available_at < self.event_time:
            raise ValueError("available_at must not precede event_time")

    def is_available_by(self, decision_time: datetime) -> bool:
        """Return whether the record was available at a proposed decision time."""
        _require_timezone(decision_time, "decision_time")
        return self.available_at <= decision_time


@dataclass(frozen=True)
class SecurityMasterRecord:
    """Provider stock-master snapshot, explicitly not a complete PIT history."""

    ts_code: str
    symbol: str
    name: str
    exchange: Exchange
    listing_status: ListingStatus
    list_date: date
    delist_date: Optional[date]
    point_in_time_confidence: PointInTimeConfidence
    source: SourceMetadata


@dataclass(frozen=True)
class DailyBarRaw:
    """Unadjusted Tushare-like bar, retaining documented provider-native units."""

    ts_code: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_chg: float
    volume_hands: float
    amount_thousand_cny: float
    source: SourceMetadata


@dataclass(frozen=True)
class DailyBar:
    """Research daily bar with both original and explicitly normalized units.

    ``close`` remains the unadjusted execution research price. Any adjusted
    research price must be created in a later, separately labelled transform.
    """

    ts_code: str
    exchange: Exchange
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    volume_hands: float
    volume_shares: float
    amount_thousand_cny: float
    turnover_cny: float
    availability: DataAvailability
    source: SourceMetadata

    @property
    def key(self) -> tuple[str, date]:
        return (self.ts_code, self.trade_date)


@dataclass(frozen=True)
class AdjustmentFactor:
    """Provider adjustment factor, never a replacement for a cash ledger."""

    ts_code: str
    trade_date: date
    factor: float
    availability: DataAvailability
    source: SourceMetadata


@dataclass(frozen=True)
class DividendEvent:
    """A provider dividend row with dates kept separate for later event logic."""

    ts_code: str
    end_date: Optional[date]
    announcement_date: Optional[date]
    implementation_announcement_date: Optional[date]
    process_status: str
    stock_dividend_per_share: Optional[float]
    cash_dividend_after_tax_per_share: Optional[float]
    cash_dividend_pre_tax_per_share: Optional[float]
    record_date: Optional[date]
    ex_date: Optional[date]
    pay_date: Optional[date]
    stock_list_date: Optional[date]
    availability: DataAvailability
    source: SourceMetadata


@dataclass(frozen=True)
class LimitBand:
    """Daily exchange price-limit band, not proof that an order can be filled."""

    ts_code: str
    trade_date: date
    up_limit: float
    down_limit: float
    source: SourceMetadata


@dataclass(frozen=True)
class TradingSession:
    """One exchange calendar day, including explicit open/closed semantics."""

    exchange: Exchange
    session_date: date
    is_open: bool
    previous_open_date: Optional[date]
    availability: DataAvailability
    source: SourceMetadata


@dataclass(frozen=True)
class SuspensionStatus:
    """Explicit suspension evidence. ``None`` is represented by absence of a record."""

    ts_code: str
    trade_date: date
    suspended: bool
    source: SourceMetadata


@dataclass(frozen=True)
class SuspensionEvent:
    """Raw S/R-style event record; it is not inferred as a complete daily state."""

    ts_code: str
    trade_date: date
    timing_code: str
    suspension_type: Optional[str]
    availability: DataAvailability
    source: SourceMetadata


@dataclass(frozen=True)
class StStatus:
    """Special-treatment state, retained as risk context rather than a fill rule."""

    ts_code: str
    name: str
    trade_date: date
    is_st: bool
    type_code: str
    label: str
    availability: DataAvailability
    source: SourceMetadata


@dataclass(frozen=True)
class DailyBasicRecord:
    """Daily valuation/share data with documented units retained in field names."""

    ts_code: str
    trade_date: date
    close: Optional[float]
    total_share_ten_thousand: Optional[float]
    float_share_ten_thousand: Optional[float]
    free_share_raw: Optional[float]
    total_market_value_ten_thousand_cny: Optional[float]
    circulating_market_value_ten_thousand_cny: Optional[float]
    availability: DataAvailability
    source: SourceMetadata


@dataclass(frozen=True)
class IndexMembership:
    """Historical membership interval with its explicit PIT confidence label."""

    index_code: str
    ts_code: str
    in_date: date
    out_date: Optional[date]
    is_current_membership_flag: bool
    availability: DataAvailability
    point_in_time_confidence: PointInTimeConfidence
    source: SourceMetadata

    def __post_init__(self) -> None:
        if self.out_date is not None and self.out_date < self.in_date:
            raise ValueError("out_date must not precede in_date")

    def is_active_on(self, as_of_date: date) -> bool:
        return self.in_date <= as_of_date and (
            self.out_date is None or as_of_date <= self.out_date
        )


@dataclass(frozen=True)
class UniverseSnapshot:
    """A versioned universe result that cannot hide unresolved PIT evidence."""

    index_code: str
    as_of_date: date
    eligible_codes: tuple[str, ...]
    unresolved_codes: tuple[str, ...]
    point_in_time_confidence: PointInTimeConfidence


@dataclass(frozen=True)
class TradabilityAssessment:
    state: TradabilityState
    reasons: tuple[TradabilityReason, ...]
