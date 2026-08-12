from math import atan, degrees

import pytest

from pyfireca.behavior._rothermel_effects import apply_scalar_spread_factors, compute_slope_factor

FM1_PACKING_RATIO = 0.034 / 32.0
FM1_BASE_ROS_M_S = 0.024733996158492002
FM1_30_PERCENT_SLOPE_ROS_M_S = 0.11632663696084798


def test_fm1_30_percent_slope_factor() -> None:
    slope_deg = degrees(atan(0.30))

    observed = compute_slope_factor(slope_deg, FM1_PACKING_RATIO)

    assert slope_deg == pytest.approx(16.69924423399362, rel=1e-14)
    assert observed == pytest.approx(3.70310726238668, rel=1e-14)


def test_fm1_slope_only_ros_matches_pinned_behave_reference() -> None:
    slope_factor = compute_slope_factor(degrees(atan(0.30)), FM1_PACKING_RATIO)

    observed = apply_scalar_spread_factors(
        FM1_BASE_ROS_M_S,
        slope_factor=slope_factor,
    )

    assert observed == pytest.approx(FM1_30_PERCENT_SLOPE_ROS_M_S, rel=1e-13)


def test_slope_factor_zero_and_invalid_boundaries() -> None:
    assert compute_slope_factor(0.0, FM1_PACKING_RATIO) == 0.0
    assert compute_slope_factor(30.0, 0.0) == 0.0

    with pytest.raises(ValueError, match="less than 90"):
        compute_slope_factor(90.0, FM1_PACKING_RATIO)
    with pytest.raises(ValueError):
        compute_slope_factor(-1.0, FM1_PACKING_RATIO)
    with pytest.raises(ValueError):
        compute_slope_factor(10.0, -0.1)


def test_scalar_effect_helper_rejects_negative_factors() -> None:
    assert apply_scalar_spread_factors(1.0) == 1.0
    assert apply_scalar_spread_factors(1.0, wind_factor=2.0, slope_factor=3.0) == 6.0

    with pytest.raises(ValueError):
        apply_scalar_spread_factors(-1.0)
    with pytest.raises(ValueError):
        apply_scalar_spread_factors(1.0, wind_factor=-0.1)
