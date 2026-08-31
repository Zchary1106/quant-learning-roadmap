"""Small, auditable functions used by the local learning labs."""

from .backtest import run_sma_backtest
from .metrics import metrics_summary
from .validation import walk_forward_sma

__all__ = ["metrics_summary", "run_sma_backtest", "walk_forward_sma"]
