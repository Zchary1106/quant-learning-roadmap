import pytest

from quantlearn.validation import walk_forward_sma


def test_walk_forward_returns_only_complete_test_folds() -> None:
    prices = [100.0 + index + (index % 5) for index in range(40)]
    result = walk_forward_sma(
        prices,
        parameter_grid=[(2, 4), (3, 6)],
        train_size=20,
        test_size=5,
        cost_bps=0,
    )
    assert len(result.folds) == 4
    assert len(result.out_of_sample_returns) == 20
    assert result.folds[0].test_start == 20
    assert result.folds[1].train_start == 5


def test_walk_forward_rejects_oversized_window() -> None:
    with pytest.raises(ValueError):
        walk_forward_sma(
            [1, 2, 3, 4, 5],
            parameter_grid=[(2, 4)],
            train_size=4,
            test_size=2,
        )
