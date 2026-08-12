from math import sqrt

import numpy as np
import pytest

from pyfireca.arrival import ConstantDirectionalSpreadRate, StaticArrivalTimeSolver
from pyfireca.behavior._surface_ellipse import build_surface_fire_ellipse
from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.evaluation import analytical_ellipse_arrival_times, arrival_error_metrics
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood


def _seed(shape: tuple[int, int], ignition: tuple[int, int]) -> np.ndarray:
    values = np.full(shape, np.inf, dtype=np.float64)
    values[ignition] = 0.0
    return values


def test_analytical_circle_matches_euclidean_center_distance() -> None:
    arrival = analytical_ellipse_arrival_times(
        (3, 3),
        cell_size_m=10.0,
        ignition=(1, 1),
        head_spread_rate_m_s=0.1,
        eccentricity=0.0,
        head_direction_deg=None,
    )

    assert arrival[1, 1] == pytest.approx(0.0)
    assert arrival[0, 1] == pytest.approx(100.0)
    assert arrival[0, 0] == pytest.approx(100.0 * sqrt(2.0))


def test_analytical_fm1_ellipse_recovers_known_head_off_axis_and_backing_times() -> None:
    head = 0.04936592733340002
    ellipse = build_surface_fire_ellipse(head, ft_min_to_m_s(100.0))
    arrival = analytical_ellipse_arrival_times(
        (3, 3),
        cell_size_m=30.0,
        ignition=(1, 1),
        head_spread_rate_m_s=head,
        eccentricity=ellipse.eccentricity,
        head_direction_deg=90.0,
    )

    assert arrival[1, 2] == pytest.approx(30.0 / head, rel=1e-13)
    assert arrival[0, 1] == pytest.approx(30.0 / 0.02921246024622574, rel=2e-10)
    assert arrival[1, 0] == pytest.approx(30.0 / 0.02074385430924511, rel=1e-13)


def test_arrival_error_metrics_return_expected_statistics() -> None:
    reference = np.array([[0.0, 10.0], [20.0, 30.0]], dtype=np.float64)
    observed = np.array([[0.0, 12.0], [18.0, 34.0]], dtype=np.float64)

    metrics = arrival_error_metrics(observed, reference)

    assert metrics.count == 4
    assert metrics.mae_s == pytest.approx(2.0)
    assert metrics.rmse_s == pytest.approx(sqrt(6.0))
    assert metrics.bias_s == pytest.approx(1.0)
    assert metrics.max_abs_error_s == pytest.approx(4.0)


def test_metrics_reject_reachability_mismatch_instead_of_dropping_it() -> None:
    reference = np.array([[0.0, 10.0]], dtype=np.float64)
    observed = np.array([[0.0, np.inf]], dtype=np.float64)

    with pytest.raises(ValueError, match="reachability differs"):
        arrival_error_metrics(observed, reference)


def test_evaluation_mask_can_exclude_known_outside_analysis_cells() -> None:
    reference = np.array([[0.0, 10.0, np.inf]], dtype=np.float64)
    observed = np.array([[0.0, 12.0, 99.0]], dtype=np.float64)
    mask = np.array([[True, True, False]], dtype=bool)

    metrics = arrival_error_metrics(observed, reference, evaluation_mask=mask)

    assert metrics.count == 2
    assert metrics.mae_s == pytest.approx(1.0)


def test_moore8_is_closer_than_vn4_to_isotropic_continuous_arrival_off_axis() -> None:
    shape = (7, 7)
    ignition = (3, 3)
    domain = np.ones(shape, dtype=bool)
    reference = analytical_ellipse_arrival_times(
        shape,
        cell_size_m=10.0,
        ignition=ignition,
        head_spread_rate_m_s=1.0,
        eccentricity=0.0,
        head_direction_deg=None,
    )

    vn4 = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=10.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    ).solve(domain, _seed(shape, ignition))
    moore8 = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=10.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    ).solve(domain, _seed(shape, ignition))

    vn4_error = arrival_error_metrics(vn4, reference)
    moore8_error = arrival_error_metrics(moore8, reference)

    assert moore8_error.rmse_s < vn4_error.rmse_s
    assert moore8_error.mae_s < vn4_error.mae_s


def test_anisotropic_reference_requires_head_direction() -> None:
    with pytest.raises(ValueError, match="requires a head_direction_deg"):
        analytical_ellipse_arrival_times(
            (3, 3),
            cell_size_m=10.0,
            ignition=(1, 1),
            head_spread_rate_m_s=1.0,
            eccentricity=0.5,
            head_direction_deg=None,
        )
