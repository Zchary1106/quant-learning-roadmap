"""Lab 1: inspect compounding and core performance metrics."""

from quantlearn.metrics import metrics_summary, simple_returns


prices = [100.0, 102.0, 101.0, 105.0, 103.0, 108.0]
returns = simple_returns(prices)

print("prices:", prices)
print("returns:", [round(value, 4) for value in returns])
for name, value in metrics_summary(returns).items():
    print(f"{name:>22}: {value:.4f}")

print("\n思考：只有 5 个日收益时，年化数字为什么极不稳定？")
