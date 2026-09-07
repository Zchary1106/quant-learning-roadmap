"""Conservative daily-bar tradability assessment with explicit uncertainty."""

from __future__ import annotations

from .contracts import (
    DailyBar,
    LimitBand,
    SuspensionStatus,
    TradeSide,
    TradingSession,
    TradabilityAssessment,
    TradabilityReason,
    TradabilityState,
)


def assess_daily_tradability(
    bar: DailyBar | None,
    side: TradeSide,
    limit_band: LimitBand | None,
    suspension: SuspensionStatus | None,
    session: TradingSession | None = None,
) -> TradabilityAssessment:
    """Assess whether available daily evidence is sufficient to assume a trade.

    A close at a price limit does not show intraday order-book availability, so
    the result is intentionally ``UNKNOWN`` rather than a fabricated fill.
    """
    reasons: list[TradabilityReason] = []
    if bar is None:
        reasons.append(TradabilityReason.MISSING_BAR)
    if session is None:
        reasons.append(TradabilityReason.MISSING_TRADING_SESSION)
    if limit_band is None:
        reasons.append(TradabilityReason.MISSING_LIMIT_BAND)
    if suspension is None:
        reasons.append(TradabilityReason.MISSING_SUSPENSION_STATUS)
    if reasons:
        return TradabilityAssessment(TradabilityState.UNKNOWN, tuple(reasons))

    if (
        bar.exchange is not session.exchange
        or bar.trade_date != session.session_date
        or bar.ts_code != limit_band.ts_code
        or bar.trade_date != limit_band.trade_date
        or bar.ts_code != suspension.ts_code
        or bar.trade_date != suspension.trade_date
    ):
        raise ValueError("bar, limit band, and suspension status must use the same key")

    if not session.is_open:
        return TradabilityAssessment(
            TradabilityState.NOT_TRADEABLE, (TradabilityReason.MARKET_CLOSED,)
        )
    if suspension.suspended:
        return TradabilityAssessment(
            TradabilityState.NOT_TRADEABLE, (TradabilityReason.SUSPENDED,)
        )
    if side is TradeSide.BUY and bar.close >= limit_band.up_limit:
        return TradabilityAssessment(
            TradabilityState.UNKNOWN, (TradabilityReason.AT_UPPER_LIMIT,)
        )
    if side is TradeSide.SELL and bar.close <= limit_band.down_limit:
        return TradabilityAssessment(
            TradabilityState.UNKNOWN, (TradabilityReason.AT_LOWER_LIMIT,)
        )
    return TradabilityAssessment(TradabilityState.TRADEABLE, ())
