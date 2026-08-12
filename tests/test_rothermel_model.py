from math import atan, degrees

import pytest

from pyfireca.behavior import (
    RothermelFuelModel,
    RothermelFuelMoisture,
    RothermelInputs,
    RothermelModel,
)
from pyfireca.behavior._units import (
    btu_lb_to_j_kg,
    feet_to_metres,
    ft_inv_to_m_inv,
    ft_min_to_m_s,
    lb_ft2_to_kg_m2,
    lb_ft3_to_kg_m3,
)

STANDARD_HEAT = tuple(btu_lb_to_j_kg(8000.0) for _ in range(6))
STANDARD_DENSITY = tuple(lb_ft3_to_kg_m3(32.0) for _ in range(6))
STANDARD_TOTAL_MINERAL = (0.0555,) * 6
STANDARD_EFFECTIVE_MINERAL = (0.01,) * 6
SLOPE_30_PERCENT_DEG = degrees(atan(0.3))


def _fm1(*, dynamic: bool = False) -> RothermelFuelModel:
    return RothermelFuelModel(
        code=1,
        depth_m=feet_to_metres(1.0),
        dead_moisture_of_extinction_fraction=0.12,
        loads_kg_m2=(lb_ft2_to_kg_m2(0.034), 0.0, 0.0, 0.0, 0.0, 0.0),
        sav_ratio_m_inv=(
            ft_inv_to_m_inv(3500.0),
            ft_inv_to_m_inv(109.0),
            ft_inv_to_m_inv(30.0),
            0.0,
            0.0,
            0.0,
        ),
        heat_content_j_kg=STANDARD_HEAT,
        particle_density_kg_m3=STANDARD_DENSITY,
        total_mineral_fraction=STANDARD_TOTAL_MINERAL,
        effective_mineral_fraction=STANDARD_EFFECTIVE_MINERAL,
        dynamic=dynamic,
    )


def _moisture() -> RothermelFuelMoisture:
    return RothermelFuelMoisture(
        dead_1h_fraction=0.05,
        dead_10h_fraction=0.05,
        dead_100h_fraction=0.05,
        live_herbaceous_fraction=1.0,
        live_woody_fraction=1.0,
    )


def _inputs(
    *,
    wind_ft_min: float = 0.0,
    wind_from_deg: float = 0.0,
    slope_deg: float = 0.0,
    aspect_deg: float = 180.0,
    dynamic: bool = False,
) -> RothermelInputs:
    return RothermelInputs(
        fuel=_fm1(dynamic=dynamic),
        moisture=_moisture(),
        midflame_wind_speed_m_s=ft_min_to_m_s(wind_ft_min),
        wind_from_direction_deg=wind_from_deg,
        slope_deg=slope_deg,
        aspect_deg=aspect_deg,
    )


def test_zero_wind_zero_slope_returns_validated_base_ros_without_fake_direction() -> None:
    result = RothermelModel().compute(_inputs())

    assert result.spread_rate_m_s == pytest.approx(0.024733996158492002, rel=1e-13)
    assert result.spread_direction_deg is None
    assert result.fireline_intensity_w_m is None
    assert result.flame_length_m is None
    assert result.diagnostics["reaction_intensity_w_m2"] == pytest.approx(
        159495.8270605292,
        rel=1e-13,
    )


def test_slope_only_matches_pinned_behave_reference_and_points_upslope() -> None:
    result = RothermelModel().compute(_inputs(slope_deg=SLOPE_30_PERCENT_DEG))

    assert result.spread_rate_m_s == pytest.approx(0.11632663696084798, rel=1e-13)
    assert result.spread_direction_deg == pytest.approx(0.0, abs=1e-12)
    assert result.diagnostics["slope_factor"] == pytest.approx(3.70310726238668, rel=1e-13)


def test_wind_only_matches_pinned_behave_reference_and_follows_downwind_push() -> None:
    result = RothermelModel().compute(
        _inputs(wind_ft_min=100.0, wind_from_deg=270.0)
    )

    assert result.spread_rate_m_s == pytest.approx(0.04936592733340002, rel=1e-13)
    assert result.spread_direction_deg == pytest.approx(90.0, abs=1e-12)
    assert result.diagnostics["wind_factor"] == pytest.approx(0.9958734939987067, rel=1e-13)


def test_perpendicular_wind_slope_matches_pinned_behave_vector_magnitude() -> None:
    result = RothermelModel().compute(
        _inputs(
            wind_ft_min=100.0,
            wind_from_deg=270.0,
            slope_deg=SLOPE_30_PERCENT_DEG,
        )
    )

    assert result.spread_rate_m_s == pytest.approx(0.11958094593841277, rel=1e-13)
    assert result.spread_direction_deg == pytest.approx(15.052373502770299, rel=1e-12)
    assert result.diagnostics["effective_factor"] == pytest.approx(
        3.834561313018457,
        rel=1e-12,
    )


def test_optional_wind_limit_caps_high_effective_wind_without_changing_direction() -> None:
    inputs = _inputs(wind_ft_min=1000.0, wind_from_deg=270.0)
    unlimited = RothermelModel().compute(inputs)
    limited = RothermelModel(use_wind_speed_limit=True).compute(inputs)

    assert unlimited.spread_rate_m_s > limited.spread_rate_m_s
    assert limited.spread_rate_m_s == pytest.approx(1.6614603649165824, rel=1e-13)
    assert limited.spread_direction_deg == pytest.approx(90.0, abs=1e-12)
    assert limited.diagnostics["wind_speed_limit_m_s"] == pytest.approx(
        3.85266521213021,
        rel=1e-13,
    )
    assert limited.diagnostics["wind_limit_enabled"] == 1.0
    assert limited.diagnostics["wind_limit_exceeded"] == 1.0
    assert unlimited.diagnostics["wind_limit_enabled"] == 0.0


def test_dynamic_fuel_still_requires_explicit_curing_before_public_compute() -> None:
    with pytest.raises(NotImplementedError, match="dynamic herbaceous"):
        RothermelModel().compute(_inputs(dynamic=True))


def test_model_option_and_input_types_are_checked() -> None:
    with pytest.raises(TypeError, match="bool"):
        RothermelModel(use_wind_speed_limit=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RothermelInputs"):
        RothermelModel().compute(object())  # type: ignore[arg-type]
