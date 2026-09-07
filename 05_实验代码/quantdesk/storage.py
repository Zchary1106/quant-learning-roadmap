"""Immutable raw snapshots and versioned SQLite storage for QuantDesk research."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from .contracts import DataAvailability, DailyBar, Exchange, SourceMetadata
from .validation import validate_daily_bars


@dataclass(frozen=True)
class SnapshotManifest:
    """Metadata needed to trace research data back to an immutable raw payload."""

    snapshot_id: str
    provider: str
    endpoint: str
    source_url: str
    retrieved_at: datetime
    parameters: Mapping[str, Any]
    fields: tuple[str, ...]
    row_count: int
    sha256: str

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip() or not self.sha256.strip():
            raise ValueError("snapshot_id and sha256 must not be empty")
        if self.row_count < 0:
            raise ValueError("row_count must be non-negative")


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _manifest_path(raw_root: Path, source: SourceMetadata) -> Path:
    return raw_root / source.snapshot_id / f"{source.endpoint}.manifest.json"


def _payload_path(raw_root: Path, source: SourceMetadata) -> Path:
    return raw_root / source.snapshot_id / f"{source.endpoint}.json"


def _manifest_to_json(manifest: SnapshotManifest) -> dict[str, Any]:
    result = asdict(manifest)
    result["retrieved_at"] = manifest.retrieved_at.isoformat()
    result["fields"] = list(manifest.fields)
    return result


def _manifest_from_json(payload: Mapping[str, Any]) -> SnapshotManifest:
    return SnapshotManifest(
        snapshot_id=str(payload["snapshot_id"]),
        provider=str(payload["provider"]),
        endpoint=str(payload["endpoint"]),
        source_url=str(payload["source_url"]),
        retrieved_at=datetime.fromisoformat(str(payload["retrieved_at"])),
        parameters=dict(payload["parameters"]),
        fields=tuple(str(field) for field in payload["fields"]),
        row_count=int(payload["row_count"]),
        sha256=str(payload["sha256"]),
    )


def write_raw_snapshot(
    payload: Any,
    *,
    source: SourceMetadata,
    parameters: Mapping[str, Any],
    fields: Iterable[str],
    row_count: int,
    raw_root: str | Path,
) -> SnapshotManifest:
    """Write a raw JSON payload once and reject different bytes at the same key.

    Repeating the exact write is idempotent. Reusing a snapshot/endpoint path for
    different bytes fails rather than overwriting research evidence.
    """
    serialized = _canonical_json_bytes(payload)
    digest = hashlib.sha256(serialized).hexdigest()
    manifest = SnapshotManifest(
        snapshot_id=source.snapshot_id,
        provider=source.provider,
        endpoint=source.endpoint,
        source_url=source.source_url,
        retrieved_at=source.retrieved_at,
        parameters=dict(parameters),
        fields=tuple(fields),
        row_count=row_count,
        sha256=digest,
    )
    root = Path(raw_root)
    payload_path = _payload_path(root, source)
    manifest_path = _manifest_path(root, source)
    payload_path.parent.mkdir(parents=True, exist_ok=True)

    if payload_path.exists():
        existing = payload_path.read_bytes()
        if existing != serialized:
            raise FileExistsError(
                f"immutable raw snapshot already exists with different contents: {payload_path}"
            )
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest missing for existing snapshot: {manifest_path}")
        return load_snapshot_manifest(manifest_path)

    if manifest_path.exists():
        raise FileExistsError(f"manifest exists without raw payload: {manifest_path}")

    payload_path.write_bytes(serialized)
    manifest_path.write_bytes(_canonical_json_bytes(_manifest_to_json(manifest)))
    return manifest


def load_snapshot_manifest(path: str | Path) -> SnapshotManifest:
    """Read and minimally validate a previously written snapshot manifest."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("snapshot manifest must be a JSON object")
    return _manifest_from_json(payload)


def _daily_bar_hash(bar: DailyBar) -> str:
    payload = {
        "ts_code": bar.ts_code,
        "exchange": bar.exchange.value,
        "trade_date": bar.trade_date.isoformat(),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "pre_close": bar.pre_close,
        "volume_hands": bar.volume_hands,
        "volume_shares": bar.volume_shares,
        "amount_thousand_cny": bar.amount_thousand_cny,
        "turnover_cny": bar.turnover_cny,
        "event_time": bar.availability.event_time.isoformat(),
        "available_at": bar.availability.available_at.isoformat(),
        "retrieved_at": bar.availability.retrieved_at.isoformat(),
        "provider": bar.source.provider,
        "endpoint": bar.source.endpoint,
        "source_url": bar.source.source_url,
        "source_retrieved_at": bar.source.retrieved_at.isoformat(),
        "snapshot_id": bar.source.snapshot_id,
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id TEXT NOT NULL PRIMARY KEY,
            provider TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_retrieved_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_bars (
            snapshot_id TEXT NOT NULL,
            ts_code TEXT NOT NULL,
            exchange TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            pre_close REAL NOT NULL,
            volume_hands REAL NOT NULL,
            volume_shares REAL NOT NULL,
            amount_thousand_cny REAL NOT NULL,
            turnover_cny REAL NOT NULL,
            event_time TEXT NOT NULL,
            available_at TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            record_sha256 TEXT NOT NULL,
            PRIMARY KEY (snapshot_id, ts_code, trade_date),
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
        );

        CREATE INDEX IF NOT EXISTS idx_daily_bars_snapshot_code_date
        ON daily_bars(snapshot_id, ts_code, trade_date);
        """
    )


def write_daily_bars(
    bars: Iterable[DailyBar], database: str | Path
) -> list[DailyBar]:
    """Append one immutable version of normalized daily bars to SQLite.

    The same records may be written repeatedly without duplication. A different
    record at an existing ``(snapshot_id, ts_code, trade_date)`` is rejected.
    """
    records = validate_daily_bars(bars)
    if not records:
        raise ValueError("at least one daily bar is required")
    snapshot_ids = {bar.source.snapshot_id for bar in records}
    if len(snapshot_ids) != 1:
        raise ValueError("one write may contain bars from exactly one snapshot_id")

    database_path = Path(database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_schema(connection)
        source = records[0].source
        existing_snapshot = connection.execute(
            "SELECT provider, endpoint, source_url, source_retrieved_at "
            "FROM snapshots WHERE snapshot_id = ?",
            (source.snapshot_id,),
        ).fetchone()
        snapshot_values = (
            source.provider,
            source.endpoint,
            source.source_url,
            source.retrieved_at.isoformat(),
        )
        if existing_snapshot is None:
            connection.execute(
                "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?)",
                (source.snapshot_id, *snapshot_values),
            )
        elif existing_snapshot != snapshot_values:
            raise ValueError("snapshot_id already exists with different source metadata")

        for bar in records:
            if bar.source != source:
                raise ValueError("all bars in a write must share source metadata")
            record_hash = _daily_bar_hash(bar)
            existing = connection.execute(
                "SELECT record_sha256 FROM daily_bars "
                "WHERE snapshot_id = ? AND ts_code = ? AND trade_date = ?",
                (bar.source.snapshot_id, bar.ts_code, bar.trade_date.isoformat()),
            ).fetchone()
            if existing is not None:
                if existing[0] != record_hash:
                    raise ValueError(
                        "immutable daily bar already exists with different contents: "
                        f"{bar.source.snapshot_id}/{bar.ts_code}/{bar.trade_date}"
                    )
                continue
            connection.execute(
                """
                INSERT INTO daily_bars (
                    snapshot_id, ts_code, exchange, trade_date, open, high, low,
                    close, pre_close, volume_hands, volume_shares,
                    amount_thousand_cny, turnover_cny, event_time, available_at,
                    retrieved_at, record_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bar.source.snapshot_id,
                    bar.ts_code,
                    bar.exchange.value,
                    bar.trade_date.isoformat(),
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.pre_close,
                    bar.volume_hands,
                    bar.volume_shares,
                    bar.amount_thousand_cny,
                    bar.turnover_cny,
                    bar.availability.event_time.isoformat(),
                    bar.availability.available_at.isoformat(),
                    bar.availability.retrieved_at.isoformat(),
                    record_hash,
                ),
            )
    return records


def read_daily_bars(
    database: str | Path,
    *,
    snapshot_id: str,
    ts_code: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[DailyBar]:
    """Read one security's fixed-version daily bars in chronological order."""
    clauses = ["b.snapshot_id = ?", "b.ts_code = ?"]
    values: list[str] = [snapshot_id, ts_code]
    if start_date is not None:
        clauses.append("b.trade_date >= ?")
        values.append(start_date)
    if end_date is not None:
        clauses.append("b.trade_date <= ?")
        values.append(end_date)
    query = (
        "SELECT b.*, s.provider, s.endpoint, s.source_url, s.source_retrieved_at "
        "FROM daily_bars AS b JOIN snapshots AS s ON b.snapshot_id = s.snapshot_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY b.trade_date"
    )
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, values).fetchall()
    results: list[DailyBar] = []
    for row in rows:
        source = SourceMetadata(
            provider=row["provider"],
            endpoint=row["endpoint"],
            source_url=row["source_url"],
            retrieved_at=datetime.fromisoformat(row["source_retrieved_at"]),
            snapshot_id=row["snapshot_id"],
        )
        availability = DataAvailability(
            event_time=datetime.fromisoformat(row["event_time"]),
            available_at=datetime.fromisoformat(row["available_at"]),
            retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
        )
        results.append(
            DailyBar(
                ts_code=row["ts_code"],
                exchange=Exchange(row["exchange"]),
                trade_date=datetime.fromisoformat(row["trade_date"]).date(),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                pre_close=row["pre_close"],
                volume_hands=row["volume_hands"],
                volume_shares=row["volume_shares"],
                amount_thousand_cny=row["amount_thousand_cny"],
                turnover_cny=row["turnover_cny"],
                availability=availability,
                source=source,
            )
        )
    return results
