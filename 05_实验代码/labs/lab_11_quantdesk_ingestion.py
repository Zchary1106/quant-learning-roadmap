"""Lab 11: run one provider-shaped response through the unified ingestion path."""

from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from quantdesk.contracts import DataAvailability, SourceMetadata
from quantdesk.ingestion import ingest_tushare_result
from quantdesk.providers.base import QueryResult
from quantdesk.storage import read_daily_bars


ROOT = Path(__file__).resolve().parents[1]
SHANGHAI = ZoneInfo("Asia/Shanghai")
payload = json.loads(
    (ROOT / "tests" / "fixtures" / "quantdesk" / "tushare_daily.json").read_text(
        encoding="utf-8"
    )
)
fields = tuple(payload)
query_result = QueryResult(
    endpoint="daily",
    fields=fields,
    rows=(payload,),
    raw_response={
        "code": 0,
        "msg": "",
        "data": {"fields": list(fields), "items": [[payload[field] for field in fields]]},
    },
)
source = SourceMetadata(
    provider="fixture",
    endpoint="daily",
    source_url="local://lab_11_quantdesk_ingestion",
    retrieved_at=datetime(2026, 9, 6, 8, tzinfo=SHANGHAI),
    snapshot_id="lab-11-fixture-20260906",
)


def availability_for(_: dict) -> DataAvailability:
    return DataAvailability(
        event_time=datetime(2026, 9, 4, 15, tzinfo=SHANGHAI),
        available_at=datetime(2026, 9, 4, 16, tzinfo=SHANGHAI),
        retrieved_at=source.retrieved_at,
    )


result = ingest_tushare_result(
    query_result,
    source=source,
    parameters={"ts_code": "600000.SH", "source": "fixture"},
    raw_root=ROOT / "data" / "quantdesk" / "raw",
    database=ROOT / "data" / "quantdesk" / "research" / "lab_11.sqlite",
    availability_for=availability_for,
)
stored = read_daily_bars(
    ROOT / "data" / "quantdesk" / "research" / "lab_11.sqlite",
    snapshot_id=source.snapshot_id,
    ts_code="600000.SH",
)
print(
    f"endpoint={result.endpoint} snapshot={result.manifest.snapshot_id} "
    f"raw_sha256={result.manifest.sha256[:12]} daily_bars={len(stored)}"
)
print("boundary: fixture only; no token, network, broker, or real order was used.")
