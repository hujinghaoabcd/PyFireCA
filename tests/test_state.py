import numpy as np
import pytest

from pyfireca.state import FireState, validate_state_array


def test_fire_state_codes_are_stable_and_unique() -> None:
    assert [int(state) for state in FireState] == [0, 1, 2, 3]
    assert len({int(state) for state in FireState}) == len(FireState)


def test_validate_state_array_accepts_valid_integer_grid() -> None:
    state = np.array(
        [
            [FireState.UNBURNABLE, FireState.UNBURNED],
            [FireState.BURNING, FireState.BURNED],
        ],
        dtype=np.uint8,
    )
    validate_state_array(state)


def test_validate_state_array_rejects_non_2d_array() -> None:
    with pytest.raises(ValueError, match="shape"):
        validate_state_array(np.array([0, 1, 2], dtype=np.uint8))


def test_validate_state_array_rejects_non_integer_dtype() -> None:
    with pytest.raises(TypeError, match="integer"):
        validate_state_array(np.zeros((2, 2), dtype=float))


def test_validate_state_array_rejects_unknown_code() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        validate_state_array(np.array([[1, 99]], dtype=np.int16))
