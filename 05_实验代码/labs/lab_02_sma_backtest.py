"""Lab 2: compare a delayed SMA strategy with buy-and-hold on synthetic data."""

import random

from quantlearn.backtest import run_sma_backtest
from quantlearn.metrics import metrics_summary


random.seed(7)
prices = [100.0]
for day in range(800):
    regime_drift = 0.0007 if (day // 160) % 2 == 0 else -0.0002
    daily_return = regime_drift + random.gauss(0.0, 0.011)
    prices.append(prices[-1] * (1.0 + daily_return))

for cost_bps in (0.0, 5.0, 20.0):
    result = run_sma_backtest(prices, fast=20, slow=80, cost_bps=cost_bps)
    strategy = metrics_summary(result["strategy_returns"])
    benchmark = metrics_summary(result["asset_returns"])
    print(f"\ncost={cost_bps:.0f} bps")
    print(f"strategy total={strategy['total_return']:.3f}, sharpe={strategy['sharpe']:.3f}, mdd={strategy['max_drawdown']:.3f}")
    print(f"buy&hold total={benchmark['total_return']:.3f}, sharpe={benchmark['sharpe']:.3f}, mdd={benchmark['max_drawdown']:.3f}")

print("\n合成数据只是时间对齐与成本实验，不是策略有效性的证据。")
