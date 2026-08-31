"""Lab 7: compare weights, risk contributions, VaR and expected shortfall."""

import numpy as np

from quantlearn.portfolio import (
    historical_var_expected_shortfall,
    inverse_volatility_weights,
    portfolio_volatility,
    risk_contributions,
)

rng = np.random.default_rng(42)
volatility = np.array([0.10, 0.18, 0.28])
correlation = np.array(
    [[1.00, 0.25, 0.10], [0.25, 1.00, 0.45], [0.10, 0.45, 1.00]]
)
covariance = np.outer(volatility, volatility) * correlation
daily_returns = rng.multivariate_normal(
    np.zeros(3), covariance / 252, size=2_000
)

portfolios = {
    "equal": np.repeat(1 / 3, 3),
    "inverse_vol": inverse_volatility_weights(volatility),
}
for name, weights in portfolios.items():
    simulated = daily_returns @ weights
    var, expected_shortfall = historical_var_expected_shortfall(simulated, 0.95)
    print(f"\n{name}: weights={weights.round(3)}")
    print(f"annualized volatility={portfolio_volatility(weights, covariance):.3f}")
    print(f"risk contributions={risk_contributions(weights, covariance).round(3)}")
    print(f"historical daily VaR 95%={var:.3%}, ES 95%={expected_shortfall:.3%}")

print("\n历史 VaR/ES 依赖样本，不能替代前瞻压力测试。")
