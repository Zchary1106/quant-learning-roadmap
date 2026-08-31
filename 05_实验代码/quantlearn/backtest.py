"""A deliberately small close-to-close moving-average backtest."""

from __future__ import annotations

from collections.abc import Iterable

from .metrics import simple_returns


def _moving_average(values: list[float], end: int, window: int) -> float | None:
    """Mean through index end inclusive, or None until the window is full."""
    start = end - window + 1
    if start < 0:
        return None
    return sum(values[start : end + 1]) / window


def run_sma_backtest(
    prices: Iterable[float], fast: int = 20, slow: int = 60, cost_bps: float = 5.0
) -> dict[str, list[float]]:
    """Long/cash SMA strategy with a full-bar execution delay.

    A signal observed at close t-1 is executed at close t and can only earn the
    close-t to close-(t+1) return. This conservative convention makes the time
    relationship visible; it is not a complete market execution model.
    """
    clean = [float(price) for price in prices]
    asset_returns = simple_returns(clean)
    if not 0 < fast < slow:
        raise ValueError("require 0 < fast < slow")
    if cost_bps < 0:
        raise ValueError("cost_bps must be non-negative")

    signals: list[float] = []
    for index in range(len(clean)):
        fast_ma = _moving_average(clean, index, fast)
        slow_ma = _moving_average(clean, index, slow)
        signals.append(1.0 if fast_ma is not None and slow_ma is not None and fast_ma > slow_ma else 0.0)

    # Return j spans price[j] -> price[j+1]. Position j uses signal[j-1].
    positions = [0.0] + signals[: max(0, len(asset_returns) - 1)]
    one_way_cost = cost_bps / 10_000.0
    previous = 0.0
    strategy_returns: list[float] = []
    for position, asset_return in zip(positions, asset_returns):
        turnover = abs(position - previous)
        strategy_returns.append(position * asset_return - turnover * one_way_cost)
        previous = position

    return {
        "asset_returns": asset_returns,
        "signals": signals,
        "positions": positions,
        "strategy_returns": strategy_returns,
    }
