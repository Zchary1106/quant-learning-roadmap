"""Transparent portfolio weighting and tail-risk calculations."""

from __future__ import annotations

import numpy as np


def inverse_volatility_weights(volatility: np.ndarray) -> np.ndarray:
    values = np.asarray(volatility, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("volatility must be a non-empty one-dimensional array")
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError("volatility must contain positive finite values")
    inverse = 1.0 / values
    return inverse / inverse.sum()


def portfolio_volatility(weights: np.ndarray, covariance: np.ndarray) -> float:
    clean_weights, clean_covariance = _validate_portfolio(weights, covariance)
    variance = float(clean_weights @ clean_covariance @ clean_weights)
    if variance < -1e-12:
        raise ValueError("covariance produces a negative portfolio variance")
    return float(np.sqrt(max(0.0, variance)))


def risk_contributions(weights: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    clean_weights, clean_covariance = _validate_portfolio(weights, covariance)
    volatility = portfolio_volatility(clean_weights, clean_covariance)
    if volatility == 0.0:
        return np.zeros_like(clean_weights)
    marginal = clean_covariance @ clean_weights / volatility
    return clean_weights * marginal


def historical_var_expected_shortfall(
    returns: np.ndarray, confidence: float = 0.95
) -> tuple[float, float]:
    values = np.asarray(returns, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("returns must be a non-empty finite one-dimensional array")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    cutoff = float(np.quantile(values, 1.0 - confidence))
    tail = values[values <= cutoff]
    return max(0.0, -cutoff), max(0.0, -float(tail.mean()))


def _validate_portfolio(
    weights: np.ndarray, covariance: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    clean_weights = np.asarray(weights, dtype=float)
    clean_covariance = np.asarray(covariance, dtype=float)
    if clean_weights.ndim != 1 or clean_weights.size == 0:
        raise ValueError("weights must be a non-empty one-dimensional array")
    if clean_covariance.shape != (clean_weights.size, clean_weights.size):
        raise ValueError("covariance shape must match weights")
    if not np.isfinite(clean_weights).all() or not np.isfinite(clean_covariance).all():
        raise ValueError("weights and covariance must contain finite values")
    if not np.allclose(clean_covariance, clean_covariance.T):
        raise ValueError("covariance must be symmetric")
    return clean_weights, clean_covariance
