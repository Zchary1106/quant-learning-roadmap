"""Explicit standard-library JSON transport for optional live health checks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import ProviderResponseError, ProviderTransportError


class UrllibJsonTransport:
    """A transport that refuses plaintext HTTP unless explicitly opted into.

    The current official Tushare Python client source uses an HTTP API endpoint.
    Because a request carries an API token, QuantDesk requires a caller to opt
    into that transport at construction time instead of doing so implicitly.
    """

    def __init__(self, *, allow_insecure_http: bool = False) -> None:
        self._allow_insecure_http = allow_insecure_http

    def post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        scheme = urlparse(url).scheme.lower()
        if scheme == "http" and not self._allow_insecure_http:
            raise ProviderTransportError(
                "refusing plaintext HTTP transport; explicitly opt in only after "
                "reviewing provider transport security"
            )
        if scheme not in {"https", "http"}:
            raise ProviderTransportError("provider URL must use HTTP or HTTPS")

        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
        except HTTPError as error:
            raise ProviderTransportError(
                f"provider transport received HTTP status {error.code}"
            ) from error
        except URLError as error:
            raise ProviderTransportError("provider transport could not reach endpoint") from error

        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderResponseError("provider transport returned invalid JSON") from error
        if not isinstance(decoded, Mapping):
            raise ProviderResponseError("provider transport returned a non-object JSON value")
        return decoded
