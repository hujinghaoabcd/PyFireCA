import pytest

from pyfireca.behavior._directions import (
    geographic_direction_from_upslope_relative_deg,
    normalize_direction_deg,
    upslope_direction_deg,
    wind_push_direction_deg,
    wind_push_relative_to_upslope_deg,
)


def test_compass_direction_normalization() -> None:
    assert normalize_direction_deg(0.0) == 0.0
    assert normalize_direction_deg(360.0) == 0.0
    assert normalize_direction_deg(-90.0) == 270.0
    assert normalize_direction_deg(450.0) == 90.0


def test_aspect_is_downslope_and_converts_to_upslope() -> None:
    assert upslope_direction_deg(0.0) == 180.0
    assert upslope_direction_deg(90.0) == 270.0
    assert upslope_direction_deg(180.0) == 0.0
    assert upslope_direction_deg(270.0) == 90.0


def test_meteorological_wind_from_converts_to_push_direction() -> None:
    assert wind_push_direction_deg(0.0) == 180.0
    assert wind_push_direction_deg(90.0) == 270.0
    assert wind_push_direction_deg(180.0) == 0.0
    assert wind_push_direction_deg(270.0) == 90.0


def test_wind_push_relative_to_upslope_special_cases() -> None:
    # North-facing downslope => upslope points south (180°).
    assert wind_push_relative_to_upslope_deg(0.0, 0.0) == 0.0
    assert wind_push_relative_to_upslope_deg(90.0, 0.0) == 90.0
    assert wind_push_relative_to_upslope_deg(180.0, 0.0) == 180.0
    assert wind_push_relative_to_upslope_deg(270.0, 0.0) == 270.0

    # East-facing downslope => upslope points west; east wind pushes west.
    assert wind_push_relative_to_upslope_deg(90.0, 90.0) == 0.0


def test_relative_direction_round_trips_to_geographic_bearing() -> None:
    relative = wind_push_relative_to_upslope_deg(90.0, 0.0)
    geographic = geographic_direction_from_upslope_relative_deg(relative, 0.0)

    assert relative == 90.0
    assert geographic == wind_push_direction_deg(90.0) == 270.0


def test_direction_helpers_reject_nonfinite_values() -> None:
    with pytest.raises(ValueError):
        normalize_direction_deg(float("nan"))
    with pytest.raises(ValueError):
        wind_push_direction_deg(float("inf"))
