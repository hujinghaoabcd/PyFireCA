import numpy as np
import pytest

from pyfireca.arrival import StaticArrivalTimeSolver
from pyfireca.behavior import (
    RothermelFuelMoisture,
    RothermelInputs,
    RothermelModel,
    get_standard_fuel_model,
)
from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.behavior.rothermel_directional import HomogeneousRothermelDirectionalSpreadRate
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood
from pyfireca.propagation import north_up_square_grid_offset_bearing_deg


def _fm1_inputs(*, wind_ft_min: float) -> RothermelInputs:
    return RothermelInputs(
        fuel=get_standard_fuel_model(1),
        moisture=RothermelFuelMoisture(
            dead_1h_fraction=0.05,
            dead_10h_fraction=0.05,
            dead_100h_fraction=0.05,
            live_herbaceous_fraction=1.0,
            live_woody_fraction=1.0,
        ),
        midflame_wind_speed_m_s=ft_min_to_m_s(wind_ft_min),
        wind_from_direction_deg=270.0,
        slope_deg=0.0,
        aspect_deg=180.0,
    )


def _seed(shape: tuple[int, int], row: int, col: int) -> np.ndarray:
    ignition = np.full(shape, np.inf, dtype=np.float64)
    ignition[row, col] = 0.0
    return ignition


@pytest.mark.parametrize(
    ("offset", "expected_bearing"),
    [
        ((-1, 0), 0.0),
        ((-1, 1), 45.0),
        ((0, 1), 90.0),
        ((1, 1), 135.0),
        ((1, 0), 180.0),
        ((1, -1), 225.0),
        ((0, -1), 270.0),
        ((-1, -1), 315.0),
    ],
)
def test_north_up_neighbor_offset_bearings(offset: tuple[int, int], expected_bearing: float) -> None:
    assert north_up_square_grid_offset_bearing_deg(offset) == pytest.approx(expected_bearing)


def test_fm1_east_head_north_off_axis_and_west_backing_rates() -> None:
    provider = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_ft_min=100.0),
    )

    assert provider.behavior_result.spread_direction_deg == pytest.approx(90.0)
    assert provider.spread_rate_m_s(0, 0, (0, 1)) == pytest.approx(
        0.04936592733340002,
        rel=1e-13,
    )
    assert provider.spread_rate_m_s(0, 0, (-1, 0)) == pytest.approx(
        0.02921246024622574,
        rel=2e-10,
    )
    assert provider.spread_rate_m_s(0, 0, (1, 0)) == pytest.approx(
        0.02921246024622574,
        rel=2e-10,
    )
    assert provider.spread_rate_m_s(0, 0, (0, -1)) == pytest.approx(
        0.02074385430924511,
        rel=1e-13,
    )


def test_fm1_diagonal_rates_follow_ellipse_angle_not_head_ros_projection() -> None:
    provider = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_ft_min=100.0),
    )

    northeast = provider.spread_rate_m_s(0, 0, (-1, 1))
    southeast = provider.spread_rate_m_s(0, 0, (1, 1))
    northwest = provider.spread_rate_m_s(0, 0, (-1, -1))
    southwest = provider.spread_rate_m_s(0, 0, (1, -1))

    assert northeast == pytest.approx(0.041067604539224284, rel=1e-13)
    assert southeast == pytest.approx(northeast, rel=1e-13)
    assert northwest == pytest.approx(southwest, rel=1e-13)
    assert northwest < northeast


def test_zero_wind_fm1_provider_is_isotropic_when_head_direction_is_undefined() -> None:
    provider = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_ft_min=0.0),
    )

    assert provider.behavior_result.spread_direction_deg is None
    expected = 0.024733996158492002
    for offset in MooreNeighborhood().offsets():
        assert provider.spread_rate_m_s(1, 1, offset) == pytest.approx(expected, rel=1e-13)


def test_arrival_solver_uses_head_and_backing_ros_on_east_west_line() -> None:
    provider = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_ft_min=100.0),
    )
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=provider,
    )
    domain = np.ones((1, 3), dtype=bool)

    arrival = solver.solve(domain, _seed((1, 3), 0, 1))

    assert arrival[0, 2] == pytest.approx(30.0 / 0.04936592733340002, rel=1e-13)
    assert arrival[0, 0] == pytest.approx(30.0 / 0.02074385430924511, rel=1e-13)
    assert arrival[0, 2] < arrival[0, 0]


def test_arrival_solver_uses_grade_b_off_axis_ros_on_north_south_line() -> None:
    provider = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_ft_min=100.0),
    )
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=provider,
    )
    domain = np.ones((3, 1), dtype=bool)

    arrival = solver.solve(domain, _seed((3, 1), 1, 0))
    expected = 30.0 / 0.02921246024622574

    assert arrival[0, 0] == pytest.approx(expected, rel=2e-10)
    assert arrival[2, 0] == pytest.approx(expected, rel=2e-10)


def test_directional_provider_honors_limited_effective_wind_for_ellipse_shape() -> None:
    unlimited = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_ft_min=1000.0),
    )
    limited = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(use_wind_speed_limit=True),
        _fm1_inputs(wind_ft_min=1000.0),
    )

    assert limited.behavior_result.diagnostics["wind_limit_exceeded"] == 1.0
    assert limited.ellipse.length_to_width_ratio < unlimited.ellipse.length_to_width_ratio
    assert limited.behavior_result.diagnostics["effective_wind_speed_m_s"] == pytest.approx(
        limited.behavior_result.diagnostics["wind_speed_limit_m_s"]
    )
