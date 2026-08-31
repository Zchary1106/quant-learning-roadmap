"""Walk-forward evaluation that selects parameters using training data only."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from .backtest import run_sma_backtest
from .metrics import sharpe_ratio


@dataclass(frozen=True)
class WalkForwardFold:
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    fast: int
    slow: int
    train_sharpe: float
    test_total_return: float


@dataclass(frozen=True)
class WalkForwardResult:
    folds: list[WalkForwardFold]
    out_of_sample_returns: list[float]


def walk_forward_sma(
    prices: Iterable[float],
    parameter_grid: Sequence[tuple[int, int]],
    train_size: int,
    test_size: int,
    cost_bps: float = 5.0,
) -> WalkForwardResult:
    clean = [float(price) for price in prices]
    if train_size < 3 or test_size <= 0:
        raise ValueError("train_size must be at least 3 and test_size must be positive")
    if not parameter_grid:
        raise ValueError("parameter_grid must not be empty")
    if any(not 0 < fast < slow < train_size for fast, slow in parameter_grid):
        raise ValueError("each pair must satisfy 0 < fast < slow < train_size")

    folds: list[WalkForwardFold] = []
    out_of_sample: list[float] = []
    train_start = 0
    while train_start + train_size + test_size <= len(clean):
        train_end = train_start + train_size
        test_end = train_end + test_size
        train_prices = clean[train_start:train_end]

        scored = []
        for fast, slow in parameter_grid:
            train_returns = run_sma_backtest(
                train_prices, fast=fast, slow=slow, cost_bps=cost_bps
            )["strategy_returns"]
            scored.append((sharpe_ratio(train_returns), fast, slow))
        train_sharpe, fast, slow = max(scored, key=lambda item: item[0])

        combined = clean[train_start:test_end]
        combined_returns = run_sma_backtest(
            combined, fast=fast, slow=slow, cost_bps=cost_bps
        )["strategy_returns"]
        test_returns = combined_returns[train_size - 1 :]
        out_of_sample.extend(test_returns)
        total_return = 1.0
        for value in test_returns:
            total_return *= 1.0 + value
        folds.append(
            WalkForwardFold(
                train_start=train_start,
                train_end=train_end - 1,
                test_start=train_end,
                test_end=test_end - 1,
                fast=fast,
                slow=slow,
                train_sharpe=train_sharpe,
                test_total_return=total_return - 1.0,
            )
        )
        train_start += test_size

    if not folds:
        raise ValueError("not enough prices for one complete train/test fold")
    return WalkForwardResult(folds=folds, out_of_sample_returns=out_of_sample)
