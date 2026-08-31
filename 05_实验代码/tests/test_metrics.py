import math

import pytest

from quantlearn.metrics import (
    calmar_ratio,
    equity_curve,
    max_drawdown,
    max_drawdown_duration,
    simple_returns,
    sortino_ratio,
)


def test_simple_returns_and_compounding() -> None:
    returns = simple_returns([100.0, 110.0, 99.0])
    assert returns == pytest.approx([0.10, -0.10])
    assert equity_curve(returns)[-1] == pytest.approx(0.99)


def test_max_drawdown_uses_running_peak() -> None:
    returns = [0.10, -0.20, 0.05]
    assert max_drawdown(returns) == pytest.approx(-0.20)


def test_drawdown_duration_resets_at_new_peak() -> None:
    assert max_drawdown_duration([-0.10, 0.05, 0.06, -0.02]) == 2


def test_downside_metrics_are_finite() -> None:
    returns = [0.02, -0.01, 0.03, -0.02]
    assert math.isfinite(sortino_ratio(returns))
    assert math.isfinite(calmar_ratio(returns))


@pytest.mark.parametrize("prices", [[], [100.0], [100.0, 0.0], [100.0, math.nan]])
def test_invalid_prices_raise(prices: list[float]) -> None:
    with pytest.raises(ValueError):
        simple_returns(prices)
