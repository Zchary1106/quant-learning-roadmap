from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from quantdesk.contracts import DataAvailability, Exchange, SourceMetadata
from quantdesk.normalize import (
    exchange_from_ts_code,
    normalize_daily_bar,
    raw_daily_bar_from_tushare,
)
from quantdesk.validation import daily_bar_quality_report, validate_daily_bars


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


def availability() -> DataAvailability:
    return DataAvailability(
        event_time=datetime(2026, 9, 4, 15, 0, tzinfo=UTC),
        available_at=datetime(2026, 9, 4, 16, 0, tzinfo=UTC),
        retrieved_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
    )


def normalized_fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return normalize_daily_bar(raw_daily_bar_from_tushare(payload, source()), availability())


def test_tushare_daily_units_are_explicitly_normalized() -> None:
    bar = normalized_fixture()
    assert bar.exchange is Exchange.SSE
    assert bar.volume_hands == pytest.approx(12_345)
    assert bar.volume_shares == pytest.approx(1_234_500)
    assert bar.amount_thousand_cny == pytest.approx(127_810.25)
    assert bar.turnover_cny == pytest.approx(127_810_250)
    assert bar.close == pytest.approx(10.35)


def test_phase_one_rejects_unsupported_exchange() -> None:
    assert exchange_from_ts_code("000001.SZ") is Exchange.SZSE
    with pytest.raises(ValueError, match="Phase 1 supports"):
        exchange_from_ts_code("430001.BJ")


def test_missing_documented_tushare_field_is_rejected() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    del payload["amount"]
    with pytest.raises(ValueError, match="missing fields: amount"):
        raw_daily_bar_from_tushare(payload, source())


def test_daily_bar_quality_gate_rejects_duplicate_and_wrong_units() -> None:
    bar = normalized_fixture()
    bad_units = bar.__class__(
        **{**vars(bar), "volume_shares": 7.0}
    )
    report = daily_bar_quality_report([bar, bad_units])
    assert report.duplicate_keys == 1
    assert report.invalid_unit_conversion == 1
    with pytest.raises(ValueError, match="daily bar quality checks failed"):
        validate_daily_bars([bar, bad_units])


def test_availability_cannot_be_used_before_it_exists() -> None:
    value = availability()
    assert value.is_available_by(datetime(2026, 9, 4, 16, 0, tzinfo=UTC))
    assert not value.is_available_by(datetime(2026, 9, 4, 15, 59, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        value.is_available_by(datetime(2026, 9, 4, 16, 0))
