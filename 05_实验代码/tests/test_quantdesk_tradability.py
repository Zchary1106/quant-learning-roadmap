from datetime import datetime, timezone
import json
from pathlib import Path

from quantdesk.contracts import (
    DataAvailability,
    LimitBand,
    SourceMetadata,
    SuspensionStatus,
    TradeSide,
    TradingSession,
    TradabilityReason,
    TradabilityState,
)
from quantdesk.normalize import normalize_daily_bar, raw_daily_bar_from_tushare
from quantdesk.tradability import assess_daily_tradability


UTC = timezone.utc
FIXTURE = Path(__file__).parent / "fixtures" / "quantdesk" / "tushare_daily.json"


def source() -> SourceMetadata:
    return SourceMetadata(
        provider="tushare_pro",
        endpoint="daily",
        source_url="https://tushare.pro/document/2?doc_id=27",
        retrieved_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
        snapshot_id="fixture-d03-20260905",
    )


def bar():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    availability = DataAvailability(
        event_time=datetime(2026, 9, 4, 15, 0, tzinfo=UTC),
        available_at=datetime(2026, 9, 4, 16, 0, tzinfo=UTC),
        retrieved_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
    )
    return normalize_daily_bar(raw_daily_bar_from_tushare(payload, source()), availability)


def session(daily_bar, is_open=True):
    return TradingSession(
        daily_bar.exchange,
        daily_bar.trade_date,
        is_open,
        daily_bar.trade_date,
        daily_bar.availability,
        source(),
    )


def test_missing_market_constraints_are_unknown_not_tradeable() -> None:
    assessment = assess_daily_tradability(bar(), TradeSide.BUY, None, None)
    assert assessment.state is TradabilityState.UNKNOWN
    assert TradabilityReason.MISSING_LIMIT_BAND in assessment.reasons
    assert TradabilityReason.MISSING_SUSPENSION_STATUS in assessment.reasons
    assert TradabilityReason.MISSING_TRADING_SESSION in assessment.reasons


def test_suspension_prevents_trade() -> None:
    daily_bar = bar()
    assessment = assess_daily_tradability(
        daily_bar,
        TradeSide.BUY,
        LimitBand("600000.SH", daily_bar.trade_date, 11.09, 9.07, source()),
        SuspensionStatus("600000.SH", daily_bar.trade_date, True, source()),
        session(daily_bar),
    )
    assert assessment.state is TradabilityState.NOT_TRADEABLE
    assert assessment.reasons == (TradabilityReason.SUSPENDED,)


def test_close_at_upper_limit_does_not_fabricate_a_buy_fill() -> None:
    daily_bar = bar()
    assessment = assess_daily_tradability(
        daily_bar,
        TradeSide.BUY,
        LimitBand("600000.SH", daily_bar.trade_date, daily_bar.close, 9.07, source()),
        SuspensionStatus("600000.SH", daily_bar.trade_date, False, source()),
        session(daily_bar),
    )
    assert assessment.state is TradabilityState.UNKNOWN
    assert assessment.reasons == (TradabilityReason.AT_UPPER_LIMIT,)


def test_complete_evidence_can_be_marked_tradeable() -> None:
    daily_bar = bar()
    assessment = assess_daily_tradability(
        daily_bar,
        TradeSide.SELL,
        LimitBand("600000.SH", daily_bar.trade_date, 11.09, 9.07, source()),
        SuspensionStatus("600000.SH", daily_bar.trade_date, False, source()),
        session(daily_bar),
    )
    assert assessment.state is TradabilityState.TRADEABLE


def test_closed_market_prevents_trade() -> None:
    daily_bar = bar()
    assessment = assess_daily_tradability(
        daily_bar,
        TradeSide.SELL,
        LimitBand("600000.SH", daily_bar.trade_date, 11.09, 9.07, source()),
        SuspensionStatus("600000.SH", daily_bar.trade_date, False, source()),
        session(daily_bar, is_open=False),
    )
    assert assessment.state is TradabilityState.NOT_TRADEABLE
    assert assessment.reasons == (TradabilityReason.MARKET_CLOSED,)
