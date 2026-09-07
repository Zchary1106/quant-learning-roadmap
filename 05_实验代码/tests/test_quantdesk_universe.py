from datetime import date, datetime, timezone

import pytest

from quantdesk.contracts import (
    DataAvailability,
    IndexMembership,
    PointInTimeConfidence,
    SourceMetadata,
)
from quantdesk.universe import build_index_universe, require_verified_point_in_time


UTC = timezone.utc


def source() -> SourceMetadata:
    return SourceMetadata(
        provider="tushare_pro",
        endpoint="index_member_all",
        source_url="https://tushare.pro/document/2?doc_id=335",
        retrieved_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
        snapshot_id="fixture-d10-20260905",
    )


def availability(hour: int) -> DataAvailability:
    return DataAvailability(
        event_time=datetime(2026, 9, 1, 9, tzinfo=UTC),
        available_at=datetime(2026, 9, 1, hour, tzinfo=UTC),
        retrieved_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )


def membership(
    ts_code: str,
    *,
    available_hour: int = 9,
    confidence: PointInTimeConfidence = PointInTimeConfidence.EFFECTIVE_INTERVAL_ONLY,
) -> IndexMembership:
    return IndexMembership(
        index_code="000300.SH",
        ts_code=ts_code,
        in_date=date(2026, 9, 1),
        out_date=None,
        availability=availability(available_hour),
        point_in_time_confidence=confidence,
        source=source(),
    )


def test_universe_surfaces_records_not_available_at_decision_time() -> None:
    result = build_index_universe(
        [membership("000001.SZ"), membership("600000.SH", available_hour=16)],
        index_code="000300.SH",
        as_of_date=date(2026, 9, 1),
        decision_time=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    assert result.eligible_codes == ("000001.SZ",)
    assert result.unresolved_codes == ("600000.SH",)
    assert result.point_in_time_confidence is PointInTimeConfidence.EFFECTIVE_INTERVAL_ONLY
    with pytest.raises(ValueError, match="unavailable"):
        require_verified_point_in_time(result)


def test_interval_only_evidence_cannot_claim_verified_pit() -> None:
    result = build_index_universe(
        [membership("000001.SZ")],
        index_code="000300.SH",
        as_of_date=date(2026, 9, 1),
        decision_time=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="not point-in-time verified"):
        require_verified_point_in_time(result)


def test_verified_evidence_can_be_used_when_no_record_is_unresolved() -> None:
    result = build_index_universe(
        [membership("000001.SZ", confidence=PointInTimeConfidence.VERIFIED)],
        index_code="000300.SH",
        as_of_date=date(2026, 9, 1),
        decision_time=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    assert require_verified_point_in_time(result) == result


def test_invalid_membership_interval_is_rejected() -> None:
    with pytest.raises(ValueError, match="out_date must not precede"):
        IndexMembership(
            index_code="000300.SH",
            ts_code="000001.SZ",
            in_date=date(2026, 9, 2),
            out_date=date(2026, 9, 1),
            availability=availability(9),
            point_in_time_confidence=PointInTimeConfidence.UNKNOWN,
            source=source(),
        )
