import pytest

from pyfireca.behavior._rothermel_effects import (
    apply_wind_speed_limit,
    compute_effective_wind_speed_m_s,
    compute_wind_factor,
    compute_wind_speed_limit_m_s,
)
from pyfireca.behavior._units import ft_inv_to_m_inv, ft_min_to_m_s

FM1_SIGMA_M_INV = ft_inv_to_m_inv(3500.0)
FM1_PACKING_RATIO = 0.034 / 32.0
FM1_OPTIMUM_PACKING_RATIO = 3.348 / 3500.0**0.8189
FM1_RELATIVE_PACKING_RATIO = FM1_PACKING_RATIO / FM1_OPTIMUM_PACKING_RATIO
FM1_BASE_ROS_M_S = 0.024733996158492002
FM1_REACTION_INTENSITY_W_M2 = 159495.8270605292


def test_effective_wind_inverts_the_same_fm1_wind_factor() -> None:
    input_wind = ft_min_to_m_s(100.0)
    wind_factor = compute_wind_factor(input_wind, FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO)

    recovered = compute_effective_wind_speed_m_s(
        wind_factor,
        FM1_SIGMA_M_INV,
        FM1_RELATIVE_PACKING_RATIO,
    )

    assert recovered == pytest.approx(input_wind, rel=1e-14)


def test_fm1_operational_wind_speed_limit_uses_native_reaction_intensity_units() -> None:
    observed = compute_wind_speed_limit_m_s(FM1_REACTION_INTENSITY_W_M2)

    assert observed == pytest.approx(3.85266521213021, rel=1e-13)
    assert observed == pytest.approx(ft_min_to_m_s(758.3986638051593), rel=1e-13)


def test_explicit_wind_limit_caps_high_effective_wind_spread() -> None:
    limit = compute_wind_speed_limit_m_s(FM1_REACTION_INTENSITY_W_M2)

    limited_spread, exceeded = apply_wind_speed_limit(
        FM1_BASE_ROS_M_S,
        ft_min_to_m_s(1000.0),
        limit,
        FM1_SIGMA_M_INV,
        FM1_RELATIVE_PACKING_RATIO,
    )

    assert exceeded
    assert limited_spread == pytest.approx(1.6614603649165824, rel=1e-13)


def test_explicit_wind_limit_leaves_sub_limit_wind_unchanged() -> None:
    limit = compute_wind_speed_limit_m_s(FM1_REACTION_INTENSITY_W_M2)
    input_wind = ft_min_to_m_s(100.0)

    spread, exceeded = apply_wind_speed_limit(
        FM1_BASE_ROS_M_S,
        input_wind,
        limit,
        FM1_SIGMA_M_INV,
        FM1_RELATIVE_PACKING_RATIO,
    )

    assert not exceeded
    expected = FM1_BASE_ROS_M_S * (
        1.0 + compute_wind_factor(input_wind, FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO)
    )
    assert spread == pytest.approx(expected, rel=1e-14)


def test_effective_wind_and_limit_boundaries_are_explicit() -> None:
    assert compute_effective_wind_speed_m_s(0.0, FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO) == 0.0
    assert compute_wind_speed_limit_m_s(0.0) == 0.0

    with pytest.raises(ValueError, match="requires positive"):
        compute_effective_wind_speed_m_s(1.0, 0.0, FM1_RELATIVE_PACKING_RATIO)
    with pytest.raises(ValueError):
        compute_wind_speed_limit_m_s(-1.0)
