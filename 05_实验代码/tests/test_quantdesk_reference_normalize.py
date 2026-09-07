from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from quantdesk.contracts import (
    DataAvailability,
    Exchange,
    PointInTimeConfidence,
    SourceMetadata,
)
from quantdesk.reference_normalize import (
    normalize_adjustment_factor,
    normalize_daily_basic,
    normalize_dividend_event,
    normalize_index_membership,
    normalize_limit_band,
    normalize_security_master,
    normalize_st_status,
    normalize_suspension_event,
    normalize_trading_session,
)


UTC = timezone.utc
FIXTURE = Path(__file__).parent / "fixtures" / "quantdesk" / "tushare_reference_records.json"


def source(endpoint: str) -> SourceMetadata:
    return SourceMetadata(
        provider="tushare_pro",
        endpoint=endpoint,
        source_url=f"https://tushare.pro/document/2?endpoint={endpoint}",
        retrieved_at=datetime(2026, 9, 6, 8, tzinfo=UTC),
        snapshot_id=f"fixture-{endpoint}-20260906",
    )


def availability() -> DataAvailability:
    return DataAvailability(
        event_time=datetime(2026, 9, 4, 15, tzinfo=UTC),
        available_at=datetime(2026, 9, 4, 16, tzinfo=UTC),
        retrieved_at=datetime(2026, 9, 6, 8, tzinfo=UTC),
    )


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_security_master_and_calendar_keep_scope_and_pit_labels() -> None:
    rows = fixture()
    security = normalize_security_master(rows["stock_basic"], source=source("stock_basic"))
    session = normalize_trading_session(
        rows["trade_cal"], source=source("trade_cal"), availability=availability()
    )
    assert security.exchange is Exchange.SSE
    assert security.point_in_time_confidence is PointInTimeConfidence.UNKNOWN
    assert session.is_open
    assert session.previous_open_date.isoformat() == "2026-09-03"


def test_reference_records_keep_timing_and_original_units() -> None:
    rows = fixture()
    adjustment = normalize_adjustment_factor(
        rows["adj_factor"], source=source("adj_factor"), availability=availability()
    )
    dividend = normalize_dividend_event(
        rows["dividend"], source=source("dividend"), availability=availability()
    )
    basics = normalize_daily_basic(
        rows["daily_basic"], source=source("daily_basic"), availability=availability()
    )
    assert adjustment.factor == pytest.approx(42.123)
    assert dividend.announcement_date.isoformat() == "2026-03-20"
    assert dividend.ex_date.isoformat() == "2026-06-11"
    assert basics.total_share_ten_thousand == pytest.approx(2_935_200)
    assert basics.free_share_raw is None
    assert basics.total_market_value_ten_thousand_cny == pytest.approx(30_379_320)


def test_market_constraint_records_are_typed_without_fill_inference() -> None:
    rows = fixture()
    limit = normalize_limit_band(rows["stk_limit"], source=source("stk_limit"))
    event = normalize_suspension_event(
        rows["suspend_d"], source=source("suspend_d"), availability=availability()
    )
    st = normalize_st_status(
        rows["stock_st"],
        source=source("stock_st"),
        availability=availability(),
        type_mapping={"S": True},
    )
    assert limit.up_limit == pytest.approx(11.09)
    assert event.timing_code == "S"
    assert st.is_st
    assert st.type_code == "S"
    assert st.label == "ST"


def test_index_membership_defaults_to_interval_only_confidence() -> None:
    membership = normalize_index_membership(
        fixture()["index_member_all"],
        source=source("index_member_all"),
        availability=availability(),
    )
    assert membership.index_code == "000300.SH"
    assert membership.is_current_membership_flag
    assert membership.point_in_time_confidence is PointInTimeConfidence.EFFECTIVE_INTERVAL_ONLY


def test_invalid_provider_status_values_are_rejected() -> None:
    bad_security = fixture()["stock_basic"] | {"list_status": "X"}
    with pytest.raises(ValueError, match="unsupported list_status"):
        normalize_security_master(bad_security, source=source("stock_basic"))

    bad_event = fixture()["suspend_d"] | {"suspend_timing": "UNKNOWN"}
    with pytest.raises(ValueError, match="suspend_timing must be S or R"):
        normalize_suspension_event(
            bad_event, source=source("suspend_d"), availability=availability()
        )

    with pytest.raises(ValueError, match="unrecognized stock_st type code"):
        normalize_st_status(
            fixture()["stock_st"],
            source=source("stock_st"),
            availability=availability(),
            type_mapping={},
        )
