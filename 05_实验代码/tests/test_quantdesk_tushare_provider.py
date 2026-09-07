from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from quantdesk.providers import (
    ProviderPermissionDenied,
    ProviderResponseError,
    ProviderTokenMissing,
    TushareProProvider,
    compact_date_windows,
)


class FakeTransport:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, Mapping[str, Any], float]] = []

    def post_json(
        self, url: str, payload: Mapping[str, Any], *, timeout_seconds: float
    ) -> Mapping[str, Any]:
        self.calls.append((url, payload, timeout_seconds))
        return self.response


class WindowTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any], float]] = []

    def post_json(
        self, url: str, payload: Mapping[str, Any], *, timeout_seconds: float
    ) -> Mapping[str, Any]:
        self.calls.append((url, payload, timeout_seconds))
        start = payload["params"]["start_date"]
        return {
            "code": 0,
            "msg": "",
            "data": {
                "fields": ["ts_code", "trade_date", "close"],
                "items": [["600000.SH", start, 10.0]],
            },
        }


def successful_response() -> Mapping[str, Any]:
    return {
        "code": 0,
        "msg": "",
        "data": {
            "fields": ["ts_code", "trade_date", "close"],
            "items": [["600000.SH", "20260904", 10.35]],
        },
    }


def test_missing_token_fails_before_transport_call() -> None:
    transport = FakeTransport(successful_response())
    provider = TushareProProvider(token=None, transport=transport)
    with pytest.raises(ProviderTokenMissing, match="no authenticated request was sent"):
        provider.query("daily")
    assert transport.calls == []


def test_environment_token_is_used_only_in_the_request_payload(monkeypatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "test-token")
    transport = FakeTransport(successful_response())
    provider = TushareProProvider.from_environment(transport=transport)

    result = provider.query(
        "daily",
        parameters={"ts_code": "600000.SH", "start_date": "20260901"},
        fields=("ts_code", "trade_date", "close"),
    )

    assert result.row_count == 1
    assert result.rows[0]["close"] == 10.35
    assert provider.last_request is not None
    assert provider.last_request.endpoint == "daily"
    assert "token" not in vars(provider.last_request)
    _, payload, _ = transport.calls[0]
    assert payload["api_name"] == "daily"
    assert payload["fields"] == "ts_code,trade_date,close"
    assert payload["params"] == {"ts_code": "600000.SH", "start_date": "20260901"}
    assert payload["token"] == "test-token"


def test_unsupported_endpoint_is_rejected_before_transport_call() -> None:
    transport = FakeTransport(successful_response())
    provider = TushareProProvider(token="test-token", transport=transport)
    with pytest.raises(ValueError, match="unsupported Tushare endpoint"):
        provider.query("not_a_real_endpoint")
    assert transport.calls == []


def test_permission_error_is_typed_and_does_not_echo_token() -> None:
    transport = FakeTransport(
        {"code": 2002, "msg": "permission denied", "data": {"fields": [], "items": []}}
    )
    provider = TushareProProvider(token="sensitive-token", transport=transport)
    with pytest.raises(ProviderPermissionDenied) as error:
        provider.query("daily")
    assert "sensitive-token" not in str(error.value)


def test_malformed_provider_rows_are_rejected() -> None:
    transport = FakeTransport(
        {
            "code": 0,
            "msg": "",
            "data": {"fields": ["ts_code", "trade_date"], "items": [["600000.SH"]]},
        }
    )
    provider = TushareProProvider(token="test-token", transport=transport)
    with pytest.raises(ProviderResponseError, match="has 1 values for 2 fields"):
        provider.query("daily")


def test_compact_date_windows_are_inclusive_and_explicit() -> None:
    assert compact_date_windows("20260901", "20260910", max_calendar_days=4) == (
        ("20260901", "20260904"),
        ("20260905", "20260908"),
        ("20260909", "20260910"),
    )
    with pytest.raises(ValueError, match="end_date must not precede"):
        compact_date_windows("20260910", "20260901", max_calendar_days=4)


def test_daily_window_requests_merge_deterministically() -> None:
    transport = WindowTransport()
    provider = TushareProProvider(token="test-token", transport=transport)
    result = provider.query_daily_windows(
        ts_code="600000.SH",
        start_date="20260901",
        end_date="20260910",
        fields=("ts_code", "trade_date", "close"),
        max_calendar_days=4,
    )
    assert [row["trade_date"] for row in result.rows] == [
        "20260901",
        "20260905",
        "20260909",
    ]
    assert [
        call[1]["params"]["start_date"] for call in transport.calls
    ] == ["20260901", "20260905", "20260909"]


def test_daily_window_requests_require_time_series_identity_fields() -> None:
    provider = TushareProProvider(token="test-token", transport=FakeTransport(successful_response()))
    with pytest.raises(ValueError, match="must include ts_code and trade_date"):
        provider.query_daily_windows(
            ts_code="600000.SH",
            start_date="20260901",
            end_date="20260904",
            fields=("close",),
        )
