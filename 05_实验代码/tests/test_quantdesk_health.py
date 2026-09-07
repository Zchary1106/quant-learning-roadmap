from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from quantdesk.health import DAILY_REQUIRED_FIELDS, check_tushare_daily_schema
from quantdesk.providers import ProviderTransportError, TushareProProvider, UrllibJsonTransport


class FakeTransport:
    def post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        return {
            "code": 0,
            "msg": "",
            "data": {
                "fields": list(DAILY_REQUIRED_FIELDS),
                "items": [["600000.SH", "20260904", 1, 1, 1, 1, 1, 0, 0, 1, 1]],
            },
        }


def test_health_check_reports_observed_daily_schema() -> None:
    provider = TushareProProvider(token="test-token", transport=FakeTransport())
    result = check_tushare_daily_schema(
        provider,
        ts_code="600000.SH",
        start_date="20260901",
        end_date="20260904",
    )
    assert result.row_count == 1
    assert result.schema_matches_design
    assert result.missing_required_fields == ()


def test_stdlib_transport_rejects_http_before_any_network_request() -> None:
    transport = UrllibJsonTransport()
    with pytest.raises(ProviderTransportError, match="refusing plaintext HTTP"):
        transport.post_json(
            "http://api.tushare.pro",
            {"api_name": "daily", "token": "test-token"},
            timeout_seconds=1,
        )
