"""Lab 3: calculate cross-sectional rank IC on a known synthetic signal."""

import numpy as np
import pandas as pd


rng = np.random.default_rng(42)
dates = pd.date_range("2022-01-31", periods=48, freq="ME")
assets = [f"asset_{index:02d}" for index in range(80)]
rows = []
for date in dates:
    factor = rng.normal(size=len(assets))
    future_return = 0.012 * factor + rng.normal(scale=0.08, size=len(assets))
    for asset, score, target in zip(assets, factor, future_return):
        rows.append((date, asset, score, target))

frame = pd.DataFrame(rows, columns=["date", "asset", "factor", "future_return"])
monthly_ic = frame.groupby("date").apply(
    lambda group: group["factor"].rank().corr(group["future_return"].rank()),
    include_groups=False,
)
print(monthly_ic.describe().round(4))
print(f"mean rank IC: {monthly_ic.mean():.4f}")
print("\n练习：把 future_return 随机打乱，确认 IC 接近 0；再模拟因子衰减。")
