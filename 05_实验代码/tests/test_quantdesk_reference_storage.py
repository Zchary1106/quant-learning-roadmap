from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from quantdesk.contracts import DataAvailability, SourceMetadata
from quantdesk.reference_normalize import (
    normalize_daily_basic,
    normalize_security_master,
    normalize_trading_session,
)
from quantdesk.storage import read_reference_records, write_reference_records


UTC = timezone.utc
FIXTURE = Path(__file__).parent / "fixtures" / "quantdesk" / "tushare_reference_records.json"


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


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


def test_reference_storage_is_idempotent_and_json_safe(tmp_path) -> None:
    security = normalize_security_master(fixture()["stock_basic"], source=source("stock_basic"))
    database = tmp_path / "reference.sqlite"
    write_reference_records([security], database)
    write_reference_records([security], database)

    stored = read_reference_records(
        database, snapshot_id=security.source.snapshot_id, endpoint="stock_basic"
    )
    assert len(stored) == 1
    assert stored[0]["record_type"] == "SecurityMasterRecord"
    assert stored[0]["record"]["exchange"] == "SSE"
    assert stored[0]["record"]["list_date"] == "1999-11-10"


def test_reference_storage_rejects_mutating_record_in_same_snapshot(tmp_path) -> None:
    security = normalize_security_master(fixture()["stock_basic"], source=source("stock_basic"))
    database = tmp_path / "reference.sqlite"
    write_reference_records([security], database)
    with pytest.raises(ValueError, match="immutable reference record already exists"):
        write_reference_records([replace(security, name="不同名称")], database)


def test_reference_storage_keeps_record_types_separate_by_endpoint(tmp_path) -> None:
    rows = fixture()
    session = normalize_trading_session(
        rows["trade_cal"], source=source("trade_cal"), availability=availability()
    )
    basics = normalize_daily_basic(
        rows["daily_basic"], source=source("daily_basic"), availability=availability()
    )
    database = tmp_path / "reference.sqlite"
    write_reference_records([session], database)
    write_reference_records([basics], database)

    sessions = read_reference_records(
        database, snapshot_id=session.source.snapshot_id, endpoint="trade_cal"
    )
    basic_rows = read_reference_records(
        database, snapshot_id=basics.source.snapshot_id, endpoint="daily_basic"
    )
    assert sessions[0]["record"]["is_open"] is True
    assert basic_rows[0]["record"]["free_share_raw"] is None
