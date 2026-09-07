"""Quality gates for normalized daily bars before research code can consume them."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from .contracts import DailyBar


@dataclass(frozen=True)
class DailyBarQualityReport:
    rows: int
    duplicate_keys: int
    invalid_ohlc: int
    nonpositive_prices: int
    invalid_numeric: int
    invalid_unit_conversion: int
    future_availability: int

    @property
    def is_valid(self) -> bool:
        return not any(
            (
                self.duplicate_keys,
                self.invalid_ohlc,
                self.nonpositive_prices,
                self.invalid_numeric,
                self.invalid_unit_conversion,
                self.future_availability,
            )
        )


def daily_bar_quality_report(bars: Iterable[DailyBar]) -> DailyBarQualityReport:
    records = list(bars)
    duplicate_keys = len(records) - len({bar.key for bar in records})
    invalid_ohlc = 0
    nonpositive_prices = 0
    invalid_numeric = 0
    invalid_unit_conversion = 0
    future_availability = 0

    for bar in records:
        numeric_values = (
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.pre_close,
            bar.volume_hands,
            bar.volume_shares,
            bar.amount_thousand_cny,
            bar.turnover_cny,
        )
        if not all(math.isfinite(value) for value in numeric_values):
            invalid_numeric += 1
            continue
        if min(bar.open, bar.high, bar.low, bar.close, bar.pre_close) <= 0:
            nonpositive_prices += 1
        if not (bar.low <= bar.open <= bar.high and bar.low <= bar.close <= bar.high):
            invalid_ohlc += 1
        if bar.volume_hands < 0 or bar.amount_thousand_cny < 0:
            invalid_numeric += 1
        if not (
            math.isclose(bar.volume_shares, bar.volume_hands * 100.0)
            and math.isclose(bar.turnover_cny, bar.amount_thousand_cny * 1_000.0)
        ):
            invalid_unit_conversion += 1
        if bar.availability.retrieved_at < bar.availability.available_at:
            future_availability += 1

    return DailyBarQualityReport(
        rows=len(records),
        duplicate_keys=duplicate_keys,
        invalid_ohlc=invalid_ohlc,
        nonpositive_prices=nonpositive_prices,
        invalid_numeric=invalid_numeric,
        invalid_unit_conversion=invalid_unit_conversion,
        future_availability=future_availability,
    )


def validate_daily_bars(bars: Iterable[DailyBar]) -> list[DailyBar]:
    """Return validated bars or reject them before they enter the research layer."""
    records = list(bars)
    report = daily_bar_quality_report(records)
    if not report.is_valid:
        failures = {
            name: value
            for name, value in vars(report).items()
            if name != "rows" and value
        }
        raise ValueError(f"daily bar quality checks failed: {failures}")
    return records
