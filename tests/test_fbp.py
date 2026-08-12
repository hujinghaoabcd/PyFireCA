"""Regression tests for the self-contained Canadian FBP implementation."""

from __future__ import annotations

import math

import pytest

from pyfireca.behavior.fbp import FBPFireType, FBPInputs, FBPModel
from pyfireca.behavior.fbp_directional import FBPEllipse


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        (
            FBPInputs(
                fuel_type="C1",
                ffmc=90,
                bui=130,
                wind_speed_10m_kmh=20,
                wind_from_direction_deg=0,
                slope_percent=15,
                aspect_deg=270,
                latitude_deg=55,
                longitude_deg=-110,
                elevation_m=0,
                julian_day=182,
            ),
            (5.556055013652935, 3139.248959888172, 0.6460598615576801, 174.69644784656137),
        ),
        (
            FBPInputs(
                fuel_type="C6",
                ffmc=94,
                bui=56,
                wind_speed_10m_kmh=25,
                wind_from_direction_deg=0,
                slope_percent=10,
                aspect_deg=180,
                latitude_deg=55,
                longitude_deg=-105,
                elevation_m=0,
                julian_day=152,
                day_of_minimum_foliar_moisture=132,
            ),
            (42.78072962636479, 36676.84532562521, 0.910886906644051, 180.0),
        ),
        (
            FBPInputs(
                fuel_type="M3",
                ffmc=87,
                bui=25,
                wind_speed_10m_kmh=10.7,
                wind_from_direction_deg=180,
                slope_percent=8,
                aspect_deg=273,
                latitude_deg=56,
                longitude_deg=-90,
                elevation_m=10,
                julian_day=130,
                percent_dead_fir=70,
            ),
            (9.355199377218359, 4002.8596994291224, 0.3159538851361391, 13.30574360051394),
        ),
        (
            FBPInputs(
                fuel_type="M4",
                ffmc=97,
                bui=80,
                wind_speed_10m_kmh=35,
                wind_from_direction_deg=180,
                slope_percent=50,
                aspect_deg=270,
                latitude_deg=56,
                longitude_deg=-90,
                elevation_m=0,
                julian_day=258,
                percent_dead_fir=30,
            ),
            (36.09755174601528, 35165.57694213195, 0.9994490848202203, 43.98157656980864),
        ),
        (
            FBPInputs(
                fuel_type="O1a",
                ffmc=95,
                bui=20,
                wind_speed_10m_kmh=35,
                wind_from_direction_deg=180,
                slope_percent=50,
                aspect_deg=270,
                latitude_deg=56,
                longitude_deg=-90,
                elevation_m=0,
                julian_day=244,
                grass_fuel_load_kg_m2=1.0,
                grass_curing_percent=90,
            ),
            (134.67179731130906, 40401.53919339272, 0.0, 40.70778526492166),
        ),
    ],
)
def test_fbp_matches_wotton_2009_reference_cases(inputs, expected):
    """Protect representative conifer, mixedwood, C6, and grass FBP cases."""

    result = FBPModel().compute_full(inputs)
    expected_ros, expected_hfi, expected_cfb, expected_direction = expected
    assert result.head_ros_m_min == pytest.approx(expected_ros, rel=1e-10, abs=1e-10)
    assert result.head_fire_intensity_kw_m == pytest.approx(expected_hfi, rel=1e-10)
    assert result.crown_fraction_burned == pytest.approx(expected_cfb, rel=1e-10, abs=1e-12)
    angular = ((result.spread_direction_deg - expected_direction + 180.0) % 360.0) - 180.0
    assert abs(angular) < 1e-10


def test_non_crowning_fuels_do_not_create_artificial_crown_fire():
    """Slash/grass/deciduous FBP classes remain non-crowning by model definition."""

    result = FBPModel().compute_full(
        FBPInputs(
            fuel_type="S1",
            ffmc=95,
            bui=130,
            wind_speed_10m_kmh=15,
            wind_from_direction_deg=180,
            slope_percent=20,
            aspect_deg=225,
            latitude_deg=50,
            longitude_deg=-90,
            julian_day=152,
        )
    )
    assert result.fire_type is FBPFireType.SURFACE
    assert result.crown_fraction_burned == 0.0
    assert result.crown_fuel_consumption_kg_m2 == 0.0


def test_fbp_generic_result_converts_native_units():
    full = FBPModel().compute_full(FBPInputs("C1", 90, 130, 20, 0, 15, 270, 55, -110, 0, 182))
    generic = FBPModel().compute(FBPInputs("C1", 90, 130, 20, 0, 15, 270, 55, -110, 0, 182))
    assert generic.spread_rate_m_s == pytest.approx(full.head_ros_m_min / 60.0)
    assert generic.fireline_intensity_w_m == pytest.approx(full.head_fire_intensity_kw_m * 1000.0)
    assert generic.diagnostics["back_ros_m_min"] == pytest.approx(full.back_ros_m_min)


def test_fbp_ellipse_preserves_head_and_back_rates():
    result = FBPModel().compute_full(FBPInputs("C1", 90, 130, 20, 0, 15, 270, 55, -110, 0, 182))
    ellipse = FBPEllipse.from_computation(result)
    assert ellipse.directional_ros_m_min(result.spread_direction_deg) == pytest.approx(
        result.head_ros_m_min
    )
    assert ellipse.directional_ros_m_min(
        (result.spread_direction_deg + 180.0) % 360.0
    ) == pytest.approx(result.back_ros_m_min)
    cross = ellipse.directional_ros_m_min((result.spread_direction_deg + 90.0) % 360.0)
    assert math.isfinite(cross)
    assert 0.0 < cross < result.head_ros_m_min


def test_fbp_nonfuel_returns_zero_behavior():
    result = FBPModel().compute_full(FBPInputs("NF", 90, 60, 10))
    assert result.fire_type is FBPFireType.NO_FIRE
    assert result.head_ros_m_min == 0.0
    assert result.head_fire_intensity_kw_m == 0.0
