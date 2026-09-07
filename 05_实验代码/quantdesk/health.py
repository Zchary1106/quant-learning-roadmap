"""Read-only, opt-in provider health checks for verified live-data onboarding."""

from __future__ import annotations

from dataclasses import dataclass

from .providers.tushare import TushareProProvider

DAILY_REQUIRED_FIELDS = (
    "ts_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_chg",
    "vol",
    "amount",
)


@dataclass(frozen=True)
class EndpointHealthCheck:
    """Observed facts from one read-only endpoint call, not a coverage guarantee."""

    endpoint: str
    parameters: dict[str, str]
    observed_fields: tuple[str, ...]
    row_count: int
    missing_required_fields: tuple[str, ...]

    @property
    def schema_matches_design(self) -> bool:
        return not self.missing_required_fields


def check_tushare_daily_schema(
    provider: TushareProProvider,
    *,
    ts_code: str,
    start_date: str,
    end_date: str,
) -> EndpointHealthCheck:
    """Call ``daily`` once and report observed schema without inferring completeness."""
    parameters = {
        "ts_code": ts_code,
        "start_date": start_date,
        "end_date": end_date,
    }
    result = provider.query("daily", parameters=parameters, fields=DAILY_REQUIRED_FIELDS)
    missing = tuple(field for field in DAILY_REQUIRED_FIELDS if field not in result.fields)
    return EndpointHealthCheck(
        endpoint=result.endpoint,
        parameters=parameters,
        observed_fields=result.fields,
        row_count=result.row_count,
        missing_required_fields=missing,
    )
