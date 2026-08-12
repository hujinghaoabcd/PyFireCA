from math import sqrt

import pytest

from pyfireca.behavior._surface_ellipse import (
    build_surface_fire_ellipse,
    compute_backing_spread_rate_m_s,
    compute_ellipse_eccentricity,
    compute_flanking_spread_rate_m_s,
    compute_surface_length_to_width_ratio,
    spread_rate_from_ignition_point_m_s,
)
from pyfireca.behavior._units import ft_min_to_m_s, mph_to_m_s


def test_surface_length_to_width_ratio_matches_pinned_behave_five_mph_case() -> None:
    observed = compute_surface_length_to_width_ratio(mph_to_m_s(5.0))

    assert observed == pytest.approx(1.5900642088709862, rel=1e-14)
    assert round(observed, 6) == pytest.approx(1.590064)


def test_zero_effective_wind_produces_circular_fire_shape() -> None:
    ellipse = build_surface_fire_ellipse(0.2, 0.0)

    assert ellipse.length_to_width_ratio == pytest.approx(1.0)
    assert ellipse.eccentricity == pytest.approx(0.0)
    assert ellipse.backing_spread_rate_m_s == pytest.approx(0.2)
    assert ellipse.flanking_spread_rate_m_s == pytest.approx(0.2)
    assert spread_rate_from_ignition_point_m_s(0.2, 0.0, 137.0) == pytest.approx(0.2)


def test_surface_length_to_width_ratio_is_capped_at_eight() -> None:
    assert compute_surface_length_to_width_ratio(mph_to_m_s(100.0)) == 8.0


def test_eccentricity_matches_geometric_definition() -> None:
    assert compute_ellipse_eccentricity(2.0) == pytest.approx(sqrt(3.0) / 2.0)


def test_fm1_100_ft_min_ellipse_dimensions_are_reproducible() -> None:
    ellipse = build_surface_fire_ellipse(
        head_spread_rate_m_s=0.04936592733340002,
        effective_wind_speed_m_s=ft_min_to_m_s(100.0),
    )

    assert ellipse.length_to_width_ratio == pytest.approx(1.0954441545539737, rel=1e-13)
    assert ellipse.eccentricity == pytest.approx(0.40824650075283053, rel=1e-13)
    assert ellipse.backing_spread_rate_m_s == pytest.approx(0.02074385430924511, rel=1e-13)
    assert ellipse.flanking_spread_rate_m_s == pytest.approx(0.032000618813467205, rel=1e-13)


def test_from_ignition_point_formula_recovers_heading_backing_and_grade_b_off_axis_ros() -> None:
    head = 0.04936592733340002
    eccentricity = 0.40824650075283053

    assert spread_rate_from_ignition_point_m_s(head, eccentricity, 0.0) == pytest.approx(
        head,
        rel=1e-13,
    )
    assert spread_rate_from_ignition_point_m_s(head, eccentricity, 180.0) == pytest.approx(
        compute_backing_spread_rate_m_s(head, eccentricity),
        rel=1e-13,
    )
    assert spread_rate_from_ignition_point_m_s(head, eccentricity, 90.0) == pytest.approx(
        0.02921246024622574,
        rel=2e-10,
    )
    assert spread_rate_from_ignition_point_m_s(head, eccentricity, 45.0) == pytest.approx(
        0.041067604539224284,
        rel=1e-13,
    )


def test_flanking_rate_matches_basic_ellipse_dimension_relation() -> None:
    assert compute_flanking_spread_rate_m_s(4.0, 2.0, 3.0) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("head", "effective_wind"),
    [
        (-1.0, 0.0),
        (1.0, -0.1),
        (float("nan"), 0.0),
        (1.0, float("inf")),
    ],
)
def test_ellipse_builder_rejects_invalid_physical_inputs(
    head: float,
    effective_wind: float,
) -> None:
    with pytest.raises(ValueError):
        build_surface_fire_ellipse(head, effective_wind)


@pytest.mark.parametrize("ratio", [0.0, 0.999, float("nan"), float("inf")])
def test_eccentricity_requires_finite_ratio_at_least_one(ratio: float) -> None:
    with pytest.raises(ValueError):
        compute_ellipse_eccentricity(ratio)


@pytest.mark.parametrize("eccentricity", [-0.1, 1.0, float("nan"), float("inf")])
def test_directional_spread_requires_valid_eccentricity(eccentricity: float) -> None:
    with pytest.raises(ValueError):
        spread_rate_from_ignition_point_m_s(1.0, eccentricity, 0.0)
