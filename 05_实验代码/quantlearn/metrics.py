"""Performance metrics with explicit assumptions and no trading dependency."""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable


def _as_finite(values: Iterable[float], name: str) -> list[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError(f"{name} must not be empty")
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{name} must contain only finite numbers")
    return result


def simple_returns(prices: Iterable[float]) -> list[float]:
    """Return consecutive simple returns; the first price has no return."""
    clean = _as_finite(prices, "prices")
    if len(clean) < 2:
        raise ValueError("at least two prices are required")
    if any(price <= 0 for price in clean):
        raise ValueError("prices must be positive")
    return [current / previous - 1.0 for previous, current in zip(clean, clean[1:])]


def equity_curve(returns: Iterable[float], initial: float = 1.0) -> list[float]:
    """Compound simple returns into a wealth curve including initial wealth."""
    clean = _as_finite(returns, "returns")
    if initial <= 0:
        raise ValueError("initial wealth must be positive")
    wealth = [float(initial)]
    for value in clean:
        if value <= -1.0:
            raise ValueError("a simple return cannot be less than or equal to -100%")
        wealth.append(wealth[-1] * (1.0 + value))
    return wealth


def annualized_return(returns: Iterable[float], periods_per_year: int = 252) -> float:
    clean = _as_finite(returns, "returns")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    ending = equity_curve(clean)[-1]
    return ending ** (periods_per_year / len(clean)) - 1.0


def annualized_volatility(returns: Iterable[float], periods_per_year: int = 252) -> float:
    clean = _as_finite(returns, "returns")
    if len(clean) < 2:
        return 0.0
    return statistics.stdev(clean) * math.sqrt(periods_per_year)


def sharpe_ratio(
    returns: Iterable[float], periods_per_year: int = 252, annual_risk_free: float = 0.0
) -> float:
    """Annualized Sharpe using a geometrically converted periodic risk-free rate."""
    clean = _as_finite(returns, "returns")
    if annual_risk_free <= -1.0:
        raise ValueError("annual_risk_free must be greater than -100%")
    periodic_rf = (1.0 + annual_risk_free) ** (1.0 / periods_per_year) - 1.0
    excess = [value - periodic_rf for value in clean]
    if len(excess) < 2:
        return 0.0
    volatility = statistics.stdev(excess)
    if volatility == 0.0:
        return 0.0
    return statistics.mean(excess) / volatility * math.sqrt(periods_per_year)


def max_drawdown(returns: Iterable[float]) -> float:
    """Return the most negative peak-to-trough drawdown (for example -0.25)."""
    wealth = equity_curve(returns)
    peak = wealth[0]
    worst = 0.0
    for value in wealth:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1.0)
    return worst


def max_drawdown_duration(returns: Iterable[float]) -> int:
    """Return the longest number of consecutive periods below a prior peak."""
    wealth = equity_curve(returns)
    peak = wealth[0]
    current = 0
    longest = 0
    for value in wealth[1:]:
        if value >= peak:
            peak = value
            current = 0
        else:
            current += 1
            longest = max(longest, current)
    return longest


def sortino_ratio(
    returns: Iterable[float], periods_per_year: int = 252, target_annual: float = 0.0
) -> float:
    """Annualized Sortino using downside deviations below a periodic target."""
    clean = _as_finite(returns, "returns")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if target_annual <= -1.0:
        raise ValueError("target_annual must be greater than -100%")
    periodic_target = (1.0 + target_annual) ** (1.0 / periods_per_year) - 1.0
    downside = [min(0.0, value - periodic_target) for value in clean]
    downside_deviation = math.sqrt(sum(value * value for value in downside) / len(downside))
    if downside_deviation == 0.0:
        return 0.0
    return (
        statistics.mean(value - periodic_target for value in clean)
        / downside_deviation
        * math.sqrt(periods_per_year)
    )


def calmar_ratio(returns: Iterable[float], periods_per_year: int = 252) -> float:
    """Annualized return divided by the absolute maximum drawdown."""
    clean = _as_finite(returns, "returns")
    drawdown = abs(max_drawdown(clean))
    if drawdown == 0.0:
        return 0.0
    return annualized_return(clean, periods_per_year) / drawdown


def metrics_summary(
    returns: Iterable[float], periods_per_year: int = 252
) -> dict[str, float | int]:
    clean = _as_finite(returns, "returns")
    wealth = equity_curve(clean)
    return {
        "total_return": wealth[-1] / wealth[0] - 1.0,
        "annualized_return": annualized_return(clean, periods_per_year),
        "annualized_volatility": annualized_volatility(clean, periods_per_year),
        "sharpe": sharpe_ratio(clean, periods_per_year),
        "sortino": sortino_ratio(clean, periods_per_year),
        "max_drawdown": max_drawdown(clean),
        "max_drawdown_duration": max_drawdown_duration(clean),
        "calmar": calmar_ratio(clean, periods_per_year),
    }
