import pytest

from pyfireca.behavior._rothermel_effects import apply_scalar_spread_factors, compute_wind_factor
from pyfireca.behavior._units import ft_inv_to_m_inv, ft_min_to_m_s

FM1_SIGMA_M_INV = ft_inv_to_m_inv(3500.0)
FM1_PACKING_RATIO = 0.034 / 32.0
FM1_OPTIMUM_PACKING_RATIO = 3.348 / 3500.0**0.8189
FM1_RELATIVE_PACKING_RATIO = FM1_PACKING_RATIO / FM1_OPTIMUM_PACKING_RATIO
FM1_BASE_ROS_M_S = 0.024733996158492002
FM1_100_FT_MIN_WIND_ROS_M_S = 0.04936592733340002


def test_fm1_100_ft_min_midflame_wind_factor() -> None:
    observed = compute_wind_factor(
        ft_min_to_m_s(100.0),
        FM1_SIGMA_M_INV,
        FM1_RELATIVE_PACKING_RATIO,
    )

    assert ft_min_to_m_s(100.0) == pytest.approx(0.508, abs=1e-15)
    assert observed == pytest.approx(0.9958734939987067, rel=1e-14)


def test_fm1_wind_only_ros_matches_expected_scalar_reference() -> None:
    wind_factor = compute_wind_factor(
        ft_min_to_m_s(100.0),
        FM1_SIGMA_M_INV,
        FM1_RELATIVE_PACKING_RATIO,
    )

    observed = apply_scalar_spread_factors(FM1_BASE_ROS_M_S, wind_factor=wind_factor)

    assert observed == pytest.approx(FM1_100_FT_MIN_WIND_ROS_M_S, rel=1e-13)


def test_wind_factor_zero_and_invalid_boundaries() -> None:
    assert compute_wind_factor(0.0, FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO) == 0.0
    assert compute_wind_factor(1.0, 0.0, FM1_RELATIVE_PACKING_RATIO) == 0.0
    assert compute_wind_factor(1.0, FM1_SIGMA_M_INV, 0.0) == 0.0

    with pytest.raises(ValueError):
        compute_wind_factor(-1.0, FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO)
    with pytest.raises(ValueError):
        compute_wind_factor(1.0, -1.0, FM1_RELATIVE_PACKING_RATIO)
    with pytest.raises(ValueError):
        compute_wind_factor(1.0, FM1_SIGMA_M_INV, -0.1)
