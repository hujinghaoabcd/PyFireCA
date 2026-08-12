import numpy as np
import pytest

from pyfireca.state import FireState, build_initial_state, validate_state_array


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


def test_build_initial_state_maps_domain_and_ignition_explicitly() -> None:
    domain = np.array([[True, True, False], [True, False, True]], dtype=bool)
    ignition = np.array([[False, True, False], [False, False, True]], dtype=bool)

    state = build_initial_state(domain, ignition)

    expected = np.array(
        [
            [FireState.UNBURNED, FireState.BURNING, FireState.UNBURNABLE],
            [FireState.UNBURNED, FireState.UNBURNABLE, FireState.BURNING],
        ],
        dtype=np.uint8,
    )
    assert np.array_equal(state, expected)


def test_build_initial_state_rejects_ignition_outside_domain() -> None:
    domain = np.array([[True, False]], dtype=bool)
    ignition = np.array([[False, True]], dtype=bool)

    with pytest.raises(ValueError, match="outside"):
        build_initial_state(domain, ignition)


def test_build_initial_state_requires_boolean_masks_and_matching_shapes() -> None:
    with pytest.raises(TypeError, match="boolean"):
        build_initial_state(np.ones((2, 2), dtype=np.uint8))  # type: ignore[arg-type]

    domain = np.ones((2, 2), dtype=bool)
    with pytest.raises(ValueError, match="does not match"):
        build_initial_state(domain, np.ones((2, 3), dtype=bool))
