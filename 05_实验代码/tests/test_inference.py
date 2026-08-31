import pytest

from quantlearn.inference import moving_block_bootstrap_mean_ci


def test_block_bootstrap_is_reproducible_and_contains_constant_mean() -> None:
    lower, upper = moving_block_bootstrap_mean_ci(
        [0.01] * 20, block_size=4, n_bootstrap=100, seed=7
    )
    assert lower == pytest.approx(0.01)
    assert upper == pytest.approx(0.01)


def test_block_size_is_validated() -> None:
    with pytest.raises(ValueError):
        moving_block_bootstrap_mean_ci([0.1, 0.2], block_size=3)
