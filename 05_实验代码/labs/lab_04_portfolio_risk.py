"""Lab 4: compare equal and inverse-volatility portfolio risk."""

import numpy as np


volatility = np.array([0.10, 0.18, 0.28])
correlation = np.array(
    [
        [1.00, 0.25, 0.10],
        [0.25, 1.00, 0.45],
        [0.10, 0.45, 1.00],
    ]
)
covariance = np.outer(volatility, volatility) * correlation

equal = np.repeat(1 / 3, 3)
inverse_vol = (1 / volatility) / (1 / volatility).sum()

for name, weights in (("equal", equal), ("inverse_vol", inverse_vol)):
    portfolio_vol = float(np.sqrt(weights @ covariance @ weights))
    marginal = covariance @ weights / portfolio_vol
    risk_contribution = weights * marginal
    print(f"{name:>12} weights={weights.round(3)}, vol={portfolio_vol:.3f}")
    print(f"{'':>12} risk contribution={risk_contribution.round(3)}")

print("\n逆波动权重不等于真正风险平价，因为它没有完整利用相关结构。")
