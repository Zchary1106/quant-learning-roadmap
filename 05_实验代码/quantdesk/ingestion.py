"""One explicit offline-first path from provider result to versioned research data."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import DataAvailability, SourceMetadata
from .normalize import normalize_daily_bar, raw_daily_bar_from_tushare
from .providers.base import QueryResult
from .reference_normalize import (
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
from .storage import (
    SnapshotManifest,
    write_daily_bars,
    write_raw_snapshot,
    write_reference_records,
)


AvailabilityFactory = Callable[[Mapping[str, Any]], DataAvailability]


@dataclass(frozen=True)
class IngestionResult:
    """Evidence produced by one provider response without claiming full coverage."""

    endpoint: str
    manifest: SnapshotManifest
    daily_bar_count: int
    reference_record_count: int


_AVAILABILITY_REQUIRED_ENDPOINTS = frozenset(
    {
        "trade_cal",
        "daily",
        "adj_factor",
        "dividend",
        "suspend_d",
        "stock_st",
        "daily_basic",
        "index_member_all",
    }
)


def _raw_envelope(result: QueryResult) -> Mapping[str, Any]:
    """Use an unmodified provider response when available, otherwise label a rebuild."""
    if result.raw_response is not None:
        return result.raw_response
    return {
        "raw_response_unavailable": True,
        "endpoint": result.endpoint,
        "fields": list(result.fields),
        "items": [
            [row.get(field) for field in result.fields]
            for row in result.rows
        ],
    }


def ingest_tushare_result(
    result: QueryResult,
    *,
    source: SourceMetadata,
    parameters: Mapping[str, Any],
    raw_root: str | Path,
    database: str | Path,
    availability_for: AvailabilityFactory | None = None,
    stock_st_type_mapping: Mapping[str, bool] | None = None,
) -> IngestionResult:
    """Persist one parsed Tushare result through its endpoint-specific contract.

    This is deliberately not a fetch function. A caller must first obtain the
    result through an explicit Provider call, then provide a source snapshot and
    availability policy. That keeps network access, raw evidence, and PIT policy
    independently auditable.
    """
    if result.endpoint != source.endpoint:
        raise ValueError("result endpoint must match source endpoint")
    if result.endpoint in _AVAILABILITY_REQUIRED_ENDPOINTS and availability_for is None:
        raise ValueError(f"{result.endpoint} ingestion requires availability_for")

    manifest = write_raw_snapshot(
        _raw_envelope(result),
        source=source,
        parameters=parameters,
        fields=result.fields,
        row_count=result.row_count,
        raw_root=raw_root,
    )

    if result.endpoint == "daily":
        assert availability_for is not None
        bars = [
            normalize_daily_bar(
                raw_daily_bar_from_tushare(row, source),
                availability_for(row),
            )
            for row in result.rows
        ]
        write_daily_bars(bars, database)
        return IngestionResult("daily", manifest, len(bars), 0)

    reference_records: list[object] = []
    for row in result.rows:
        if result.endpoint == "stock_basic":
            reference_records.append(normalize_security_master(row, source=source))
        elif result.endpoint == "trade_cal":
            assert availability_for is not None
            reference_records.append(
                normalize_trading_session(
                    row, source=source, availability=availability_for(row)
                )
            )
        elif result.endpoint == "adj_factor":
            assert availability_for is not None
            reference_records.append(
                normalize_adjustment_factor(
                    row, source=source, availability=availability_for(row)
                )
            )
        elif result.endpoint == "dividend":
            assert availability_for is not None
            reference_records.append(
                normalize_dividend_event(
                    row, source=source, availability=availability_for(row)
                )
            )
        elif result.endpoint == "stk_limit":
            reference_records.append(normalize_limit_band(row, source=source))
        elif result.endpoint == "suspend_d":
            assert availability_for is not None
            reference_records.append(
                normalize_suspension_event(
                    row, source=source, availability=availability_for(row)
                )
            )
        elif result.endpoint == "stock_st":
            if stock_st_type_mapping is None:
                raise ValueError("stock_st ingestion requires stock_st_type_mapping")
            assert availability_for is not None
            reference_records.append(
                normalize_st_status(
                    row,
                    source=source,
                    availability=availability_for(row),
                    type_mapping=stock_st_type_mapping,
                )
            )
        elif result.endpoint == "daily_basic":
            assert availability_for is not None
            reference_records.append(
                normalize_daily_basic(
                    row, source=source, availability=availability_for(row)
                )
            )
        elif result.endpoint == "index_member_all":
            assert availability_for is not None
            reference_records.append(
                normalize_index_membership(
                    row, source=source, availability=availability_for(row)
                )
            )
        else:
            raise ValueError(f"unsupported Tushare ingestion endpoint: {result.endpoint}")

    if reference_records:
        write_reference_records(reference_records, database)  # type: ignore[arg-type]
    return IngestionResult(result.endpoint, manifest, 0, len(reference_records))
