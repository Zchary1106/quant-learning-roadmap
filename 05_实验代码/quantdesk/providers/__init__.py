"""Provider contracts and offline-first adapters."""

from .base import (
    DataProviderError,
    ProviderPermissionDenied,
    ProviderResponseError,
    ProviderTokenMissing,
    ProviderTransport,
    ProviderTransportError,
    QueryResult,
)
from .tushare import TushareProProvider, compact_date_windows
from .urllib_transport import UrllibJsonTransport

__all__ = [
    "DataProviderError",
    "ProviderPermissionDenied",
    "ProviderResponseError",
    "ProviderTokenMissing",
    "ProviderTransport",
    "ProviderTransportError",
    "QueryResult",
    "TushareProProvider",
    "UrllibJsonTransport",
    "compact_date_windows",
]
