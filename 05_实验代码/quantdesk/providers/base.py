"""Provider-neutral interfaces. Network I/O is injected, never implicit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol


class DataProviderError(RuntimeError):
    """Base class for safe, non-secret-bearing provider errors."""


class ProviderTokenMissing(DataProviderError):
    """Raised before an authenticated request is attempted without a token."""


class ProviderTransportError(DataProviderError):
    """Raised when an injected transport cannot complete a request."""


class ProviderPermissionDenied(DataProviderError):
    """Raised when a provider rejects a request due to account entitlement."""


class ProviderResponseError(DataProviderError):
    """Raised when a provider response is malformed or semantically failed."""


class ProviderTransport(Protocol):
    """Small HTTP seam that tests can replace without making network calls."""

    def post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        """Send a JSON request and return decoded JSON."""


@dataclass(frozen=True)
class QueryResult:
    """Tabular result detached from a provider-specific DataFrame implementation."""

    endpoint: str
    fields: tuple[str, ...]
    rows: tuple[Mapping[str, Any], ...]

    @property
    def row_count(self) -> int:
        return len(self.rows)


def require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProviderResponseError(f"{name} must be an object")
    return value


def require_sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProviderResponseError(f"{name} must be an array")
    return value
