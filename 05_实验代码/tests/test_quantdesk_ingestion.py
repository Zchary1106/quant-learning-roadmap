from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from quantdesk.contracts import DataAvailability, SourceMetadata
from quantdesk.ingestion import ingest_tushare_result
from quantdesk.providers.base import QueryResult
from quantdesk.storage import read_daily_bars, read_reference_records


UTC = timezone.utc
ROOT = Path(__file__).parent / "fixtures" / "quantdesk"


def source(endpoint: str, snapshot_id: str) -> SourceMetadata:
    return SourceMetadata(
        provider="tushare_pro",
        endpoint=endpoint,
        source_url=f"https://tushare.pro/document/2?endpoint={endpoint}",
        retrieved_at=datetime(2026, 9, 6, 8, tzinfo=UTC),
        snapshot_id=snapshot_id,
    )


def availability(_: dict) -> DataAvailability:
    return DataAvailability(
        event_time=datetime(2026, 9, 4, 15, tzinfo=UTC),
        available_at=datetime(2026, 9, 4, 16, tzinfo=UTC),
        retrieved_at=datetime(2026, 9, 6, 8, tzinfo=UTC),
    )


def result(endpoint: str, row: dict) -> QueryResult:
    fields = tuple(row)
    return QueryResult(
        endpoint=endpoint,
        fields=fields,
        rows=(row,),
        raw_response={"code": 0, "msg": "", "data": {"fields": list(fields), "items": [[row[key] for key in fields]]}},
    )


def fixture(name: str) -> dict:
    filename = "tushare_daily.json" if name == "daily" else "tushare_reference_records.json"
    values = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    return values if name == "daily" else values[name]


def test_daily_ingestion_writes_raw_evidence_and_research_bar(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    database = tmp_path / "research.sqlite"
    result_value = result("daily", fixture("daily"))
    source_value = source("daily", "ingest-daily-20260906")

    ingested = ingest_tushare_result(
        result_value,
        source=source_value,
        parameters={"ts_code": "600000.SH"},
        raw_root=raw_root,
        database=database,
        availability_for=availability,
    )

    stored = read_daily_bars(
        database, snapshot_id=source_value.snapshot_id, ts_code="600000.SH"
    )
    assert ingested.daily_bar_count == 1
    assert ingested.reference_record_count == 0
    assert (raw_root / source_value.snapshot_id / "daily.manifest.json").is_file()
    assert stored[0].turnover_cny == pytest.approx(127_810_250)


def test_reference_ingestion_writes_typed_versioned_record(tmp_path) -> None:
    source_value = source("daily_basic", "ingest-basic-20260906")
    ingested = ingest_tushare_result(
        result("daily_basic", fixture("daily_basic")),
        source=source_value,
        parameters={"ts_code": "600000.SH"},
        raw_root=tmp_path / "raw",
        database=tmp_path / "research.sqlite",
        availability_for=availability,
    )
    stored = read_reference_records(
        tmp_path / "research.sqlite",
        snapshot_id=source_value.snapshot_id,
        endpoint="daily_basic",
    )
    assert ingested.daily_bar_count == 0
    assert ingested.reference_record_count == 1
    assert stored[0]["record_type"] == "DailyBasicRecord"


def test_ingestion_requires_explicit_time_policy_for_time_sensitive_endpoints(tmp_path) -> None:
    with pytest.raises(ValueError, match="daily ingestion requires availability_for"):
        ingest_tushare_result(
            result("daily", fixture("daily")),
            source=source("daily", "missing-availability"),
            parameters={},
            raw_root=tmp_path / "raw",
            database=tmp_path / "research.sqlite",
        )


def test_stock_st_ingestion_requires_verified_type_mapping(tmp_path) -> None:
    with pytest.raises(ValueError, match="stock_st ingestion requires stock_st_type_mapping"):
        ingest_tushare_result(
            result("stock_st", fixture("stock_st")),
            source=source("stock_st", "missing-st-map"),
            parameters={},
            raw_root=tmp_path / "raw",
            database=tmp_path / "research.sqlite",
            availability_for=availability,
        )


def test_ingestion_rejects_endpoint_metadata_mismatch(tmp_path) -> None:
    with pytest.raises(ValueError, match="result endpoint must match"):
        ingest_tushare_result(
            result("daily", fixture("daily")),
            source=source("daily_basic", "wrong-endpoint"),
            parameters={},
            raw_root=tmp_path / "raw",
            database=tmp_path / "research.sqlite",
            availability_for=availability,
        )
