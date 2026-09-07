"""Tushare Pro adapter with injected transport and no persisted credentials.

The official Python client stores tokens when ``set_token`` is used. QuantDesk
does not call that method: callers pass a token explicitly or use
``TUSHARE_TOKEN`` for a single process. This module intentionally supplies no
network transport, so importing it cannot make an authenticated request.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .base import (
    ProviderPermissionDenied,
    ProviderResponseError,
    ProviderTokenMissing,
    ProviderTransport,
    ProviderTransportError,
    QueryResult,
    require_mapping,
    require_sequence,
)

TUSHARE_PRO_URL = "http://api.tushare.pro"

SUPPORTED_ENDPOINTS = frozenset(
    {
        "stock_basic",
        "trade_cal",
        "daily",
        "adj_factor",
        "dividend",
        "stk_limit",
        "suspend_d",
        "stock_st",
        "daily_basic",
        "index_member_all",
    }
)


@dataclass(frozen=True)
class TushareRequestAudit:
    """Safe request metadata. It deliberately has no token field."""

    endpoint: str
    parameters: Mapping[str, Any]
    requested_fields: tuple[str, ...]


class TushareProProvider:
    """A strict adapter around Tushare's JSON query request shape.

    The adapter returns provider-neutral mappings. It does not silently infer
    account permissions, row completeness, point-in-time coverage, or a fill
    model from a successful query.
    """

    def __init__(
        self,
        *,
        token: str | None,
        transport: ProviderTransport,
        base_url: str = TUSHARE_PRO_URL,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._token = (token or "").strip()
        self._transport = transport
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self.last_request: TushareRequestAudit | None = None
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not base_url.strip():
            raise ValueError("base_url must not be empty")

    @classmethod
    def from_environment(
        cls,
        *,
        transport: ProviderTransport,
        environment: Mapping[str, str] | None = None,
        base_url: str = TUSHARE_PRO_URL,
        timeout_seconds: float = 10.0,
    ) -> "TushareProProvider":
        """Build from the process environment without writing credentials to disk."""
        values = os.environ if environment is None else environment
        return cls(
            token=values.get("TUSHARE_TOKEN"),
            transport=transport,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

    @property
    def token_configured(self) -> bool:
        return bool(self._token)

    def query(
        self,
        endpoint: str,
        *,
        parameters: Mapping[str, Any] | None = None,
        fields: Sequence[str] = (),
    ) -> QueryResult:
        """Issue one explicit provider query through the injected transport."""
        if endpoint not in SUPPORTED_ENDPOINTS:
            raise ValueError(f"unsupported Tushare endpoint: {endpoint}")
        if not self._token:
            raise ProviderTokenMissing(
                "TUSHARE_TOKEN is not configured; no authenticated request was sent"
            )

        normalized_parameters = dict(parameters or {})
        normalized_fields = tuple(fields)
        if any(not field.strip() for field in normalized_fields):
            raise ValueError("field names must not be empty")
        self.last_request = TushareRequestAudit(
            endpoint=endpoint,
            parameters=normalized_parameters,
            requested_fields=normalized_fields,
        )
        payload = {
            "api_name": endpoint,
            "token": self._token,
            "params": normalized_parameters,
            "fields": ",".join(normalized_fields),
        }
        try:
            response = self._transport.post_json(
                self._base_url, payload, timeout_seconds=self._timeout_seconds
            )
        except ProviderTransportError:
            raise
        except Exception as error:
            raise ProviderTransportError(
                f"Tushare transport failed for endpoint {endpoint}"
            ) from error
        return self._parse_response(endpoint, response)

    def _parse_response(self, endpoint: str, response: Mapping[str, Any]) -> QueryResult:
        body = require_mapping(response, "Tushare response")
        code = body.get("code")
        if code != 0:
            message = str(body.get("msg", "provider returned an unspecified error"))
            if code in {2002, 2003, 2010}:
                raise ProviderPermissionDenied(
                    f"Tushare denied endpoint {endpoint}: {message}"
                )
            raise ProviderResponseError(f"Tushare error for endpoint {endpoint}: {message}")

        data = require_mapping(body.get("data"), "Tushare response.data")
        fields = require_sequence(data.get("fields"), "Tushare response.data.fields")
        items = require_sequence(data.get("items"), "Tushare response.data.items")
        normalized_fields = tuple(str(field) for field in fields)
        if not normalized_fields or any(not field for field in normalized_fields):
            raise ProviderResponseError("Tushare response has invalid fields")

        rows: list[Mapping[str, Any]] = []
        for index, item in enumerate(items):
            values = require_sequence(item, f"Tushare response.data.items[{index}]")
            if len(values) != len(normalized_fields):
                raise ProviderResponseError(
                    f"Tushare row {index} has {len(values)} values for "
                    f"{len(normalized_fields)} fields"
                )
            rows.append(dict(zip(normalized_fields, values)))
        return QueryResult(endpoint=endpoint, fields=normalized_fields, rows=tuple(rows))
