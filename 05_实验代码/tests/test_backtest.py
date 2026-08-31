import pytest

from quantlearn.backtest import run_sma_backtest


def test_signal_has_full_bar_execution_delay() -> None:
    result = run_sma_backtest([1, 1, 1, 2, 4, 8], fast=2, slow=3, cost_bps=0)
    first_long_signal = result["signals"].index(1.0)
    first_long_position = result["positions"].index(1.0)
    assert first_long_position == first_long_signal + 1


def test_entry_cost_is_charged_on_position_change() -> None:
    result = run_sma_backtest([1, 1, 1, 2, 2, 2], fast=2, slow=3, cost_bps=10)
    entry = result["positions"].index(1.0)
    assert result["strategy_returns"][entry] == pytest.approx(-0.001)


def test_window_order_is_validated() -> None:
    with pytest.raises(ValueError):
        run_sma_backtest([1, 2, 3], fast=3, slow=2)
