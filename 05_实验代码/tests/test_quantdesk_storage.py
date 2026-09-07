from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

import pytest

from quantdesk.contracts import DataAvailability, SourceMetadata
from quantdesk.normalize import normalize_daily_bar, raw_daily_bar_from_tushare
from quantdesk.storage import (
    load_snapshot_manifest,
    read_daily_bars,
    write_daily_bars,
    write_raw_snapshot,
)


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


def daily_bar():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return normalize_daily_bar(
        raw_daily_bar_from_tushare(payload, source()),
        DataAvailability(
            event_time=datetime(2026, 9, 4, 15, 0, tzinfo=UTC),
            available_at=datetime(2026, 9, 4, 16, 0, tzinfo=UTC),
            retrieved_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
        ),
    )


def test_raw_snapshot_is_idempotent_and_has_manifest(tmp_path) -> None:
    payload = {"data": [["600000.SH", "20260904", 10.35]]}
    manifest = write_raw_snapshot(
        payload,
        source=source(),
        parameters={"ts_code": "600000.SH"},
        fields=("ts_code", "trade_date", "close"),
        row_count=1,
        raw_root=tmp_path,
    )
    repeated = write_raw_snapshot(
        payload,
        source=source(),
        parameters={"ts_code": "600000.SH"},
        fields=("ts_code", "trade_date", "close"),
        row_count=1,
        raw_root=tmp_path,
    )
    loaded = load_snapshot_manifest(
        tmp_path / source().snapshot_id / "daily.manifest.json"
    )
    assert manifest == repeated == loaded
    assert len(manifest.sha256) == 64


def test_raw_snapshot_refuses_overwrite_with_different_evidence(tmp_path) -> None:
    common = {
        "source": source(),
        "parameters": {},
        "fields": (),
        "row_count": 0,
        "raw_root": tmp_path,
    }
    write_raw_snapshot({"data": []}, **common)
    with pytest.raises(FileExistsError, match="immutable raw snapshot"):
        write_raw_snapshot({"data": ["different"]}, **common)


def test_sqlite_store_is_versioned_and_idempotent(tmp_path) -> None:
    database = tmp_path / "research.sqlite"
    bar = daily_bar()
    write_daily_bars([bar], database)
    write_daily_bars([bar], database)

    with sqlite3.connect(database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0]
        snapshot_count = connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    stored = read_daily_bars(
        database, snapshot_id=bar.source.snapshot_id, ts_code=bar.ts_code
    )
    assert count == 1
    assert snapshot_count == 1
    assert stored == [bar]


def test_sqlite_store_refuses_mutating_an_existing_version(tmp_path) -> None:
    database = tmp_path / "research.sqlite"
    bar = daily_bar()
    write_daily_bars([bar], database)
    changed = bar.__class__(**{**vars(bar), "close": 10.36})
    with pytest.raises(ValueError, match="immutable daily bar already exists"):
        write_daily_bars([changed], database)
