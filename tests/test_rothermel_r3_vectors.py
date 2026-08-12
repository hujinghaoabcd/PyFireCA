from math import degrees, hypot

import pytest

from pyfireca.behavior._rothermel_vectors import combine_wind_slope_effects


def test_zero_effects_preserve_base_spread_and_upslope_reference() -> None:
    result = combine_wind_slope_effects(
        2.0,
        wind_factor=0.0,
        slope_factor=0.0,
        wind_push_relative_to_upslope_deg=127.0,
    )

    assert result.spread_rate_m_s == 2.0
    assert result.effective_factor == 0.0
    assert result.direction_relative_to_upslope_deg == 0.0


def test_slope_only_points_upslope() -> None:
    result = combine_wind_slope_effects(
        2.0,
        wind_factor=0.0,
        slope_factor=3.0,
        wind_push_relative_to_upslope_deg=90.0,
    )

    assert result.spread_rate_m_s == 8.0
    assert result.effective_factor == 3.0
    assert result.direction_relative_to_upslope_deg == 0.0


def test_wind_only_follows_wind_push_direction() -> None:
    result = combine_wind_slope_effects(
        2.0,
        wind_factor=4.0,
        slope_factor=0.0,
        wind_push_relative_to_upslope_deg=90.0,
    )

    assert result.spread_rate_m_s == 10.0
    assert result.effective_factor == 4.0
    assert result.direction_relative_to_upslope_deg == pytest.approx(90.0)


def test_collinear_same_direction_reduces_to_scalar_sum() -> None:
    result = combine_wind_slope_effects(
        2.0,
        wind_factor=4.0,
        slope_factor=3.0,
        wind_push_relative_to_upslope_deg=0.0,
    )

    assert result.spread_rate_m_s == 16.0
    assert result.effective_factor == 7.0
    assert result.direction_relative_to_upslope_deg == 0.0


def test_opposite_effects_follow_the_stronger_vector() -> None:
    upslope_wins = combine_wind_slope_effects(
        2.0,
        wind_factor=2.0,
        slope_factor=3.0,
        wind_push_relative_to_upslope_deg=180.0,
    )
    wind_wins = combine_wind_slope_effects(
        2.0,
        wind_factor=4.0,
        slope_factor=3.0,
        wind_push_relative_to_upslope_deg=180.0,
    )

    assert upslope_wins.spread_rate_m_s == pytest.approx(4.0)
    assert upslope_wins.direction_relative_to_upslope_deg == pytest.approx(0.0)
    assert wind_wins.spread_rate_m_s == pytest.approx(4.0)
    assert wind_wins.direction_relative_to_upslope_deg == pytest.approx(180.0)


def test_perpendicular_effects_use_vector_magnitude_not_scalar_sum() -> None:
    result = combine_wind_slope_effects(
        2.0,
        wind_factor=4.0,
        slope_factor=3.0,
        wind_push_relative_to_upslope_deg=90.0,
    )

    assert result.effective_factor == pytest.approx(hypot(3.0, 4.0))
    assert result.spread_rate_m_s == pytest.approx(12.0)
    assert result.direction_relative_to_upslope_deg == pytest.approx(degrees(0.9272952180016122))
    assert result.spread_rate_m_s < 2.0 * (1.0 + 3.0 + 4.0)


def test_angles_are_normalized_and_invalid_values_rejected() -> None:
    wrapped = combine_wind_slope_effects(
        1.0,
        wind_factor=1.0,
        slope_factor=0.0,
        wind_push_relative_to_upslope_deg=450.0,
    )
    assert wrapped.direction_relative_to_upslope_deg == pytest.approx(90.0)

    with pytest.raises(ValueError):
        combine_wind_slope_effects(
            -1.0,
            wind_factor=1.0,
            slope_factor=1.0,
            wind_push_relative_to_upslope_deg=0.0,
        )
    with pytest.raises(ValueError):
        combine_wind_slope_effects(
            1.0,
            wind_factor=-1.0,
            slope_factor=1.0,
            wind_push_relative_to_upslope_deg=0.0,
        )
