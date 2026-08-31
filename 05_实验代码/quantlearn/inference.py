"""Dependence-aware statistical helpers for educational experiments."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def moving_block_bootstrap_mean_ci(
    values: Iterable[float],
    block_size: int,
    n_bootstrap: int = 2_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> tuple[float, float]:
    """Estimate a percentile CI for the mean using circular moving blocks."""
    sample = np.asarray(list(values), dtype=float)
    if sample.size < 2 or not np.isfinite(sample).all():
        raise ValueError("values must contain at least two finite numbers")
    if not 1 <= block_size <= sample.size:
        raise ValueError("block_size must be between 1 and the sample size")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    rng = np.random.default_rng(seed)
    block_count = int(np.ceil(sample.size / block_size))
    offsets = np.arange(block_size)
    means = np.empty(n_bootstrap)
    for index in range(n_bootstrap):
        starts = rng.integers(0, sample.size, size=block_count)
        indices = (starts[:, None] + offsets) % sample.size
        resample = sample[indices.ravel()[: sample.size]]
        means[index] = resample.mean()

    tail = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(means, [tail, 1.0 - tail])
    return float(lower), float(upper)
