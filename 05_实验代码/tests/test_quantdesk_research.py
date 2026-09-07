from datetime import datetime, timezone
from dataclasses import replace
import json
from pathlib import Path

import pytest

from quantdesk.contracts import DataAvailability, SourceMetadata
from quantdesk.normalize import normalize_daily_bar, raw_daily_bar_from_tushare
from quantdesk.research import bars_to_ohlcv_frame, bars_to_research_frame


UTC = timezone.utc
FIXTURE = Path(__file__).parent / "fixtures" / "quantdesk" / "tushare_daily.json"


def bar(snapshot_id: str = "fixture-d03-20260905"):
    source = SourceMetadata(
        provider="tushare_pro",
        endpoint="daily",
        source_url="https://tushare.pro/document/2?doc_id=27",
        retrieved_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
        snapshot_id=snapshot_id,
    )
    availability = DataAvailability(
        event_time=datetime(2026, 9, 4, 15, tzinfo=UTC),
        available_at=datetime(2026, 9, 4, 16, tzinfo=UTC),
        retrieved_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return normalize_daily_bar(raw_daily_bar_from_tushare(payload, source), availability)


def test_research_frame_preserves_snapshot_and_availability() -> None:
    frame = bars_to_research_frame([bar()])
    assert frame.loc[0, "snapshot_id"] == "fixture-d03-20260905"
    assert frame.loc[0, "available_at"].tzinfo is not None
    assert frame.loc[0, "volume_shares"] == pytest.approx(1_234_500)


def test_ohlcv_bridge_uses_unadjusted_close_and_share_volume() -> None:
    frame = bars_to_ohlcv_frame([bar()])
    assert frame.columns.tolist() == ["date", "open", "high", "low", "close", "volume"]
    assert frame.loc[0, "close"] == pytest.approx(10.35)
    assert frame.loc[0, "volume"] == pytest.approx(1_234_500)


def test_research_frame_rejects_mixed_snapshot_versions() -> None:
    other_snapshot_bar = replace(bar("snapshot-b"), ts_code="600001.SH")
    with pytest.raises(ValueError, match="exactly one snapshot_id"):
        bars_to_research_frame([bar("snapshot-a"), other_snapshot_bar])
