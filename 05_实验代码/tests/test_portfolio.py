import numpy as np
import pytest

from quantlearn.portfolio import (
    historical_var_expected_shortfall,
    inverse_volatility_weights,
    portfolio_volatility,
    risk_contributions,
)


def test_inverse_volatility_weights_sum_to_one() -> None:
    weights = inverse_volatility_weights(np.array([0.1, 0.2, 0.4]))
    assert weights.sum() == pytest.approx(1.0)
    assert weights.tolist() == pytest.approx([4 / 7, 2 / 7, 1 / 7])


def test_risk_contributions_sum_to_portfolio_volatility() -> None:
    weights = np.array([0.5, 0.5])
    covariance = np.array([[0.04, 0.01], [0.01, 0.09]])
    contributions = risk_contributions(weights, covariance)
    assert contributions.sum() == pytest.approx(portfolio_volatility(weights, covariance))


def test_expected_shortfall_is_at_least_var() -> None:
    var, expected_shortfall = historical_var_expected_shortfall(
        np.array([-0.10, -0.04, -0.02, 0.01, 0.03]), confidence=0.8
    )
    assert expected_shortfall >= var >= 0.0
