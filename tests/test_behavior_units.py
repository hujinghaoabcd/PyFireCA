import pytest

from pyfireca.behavior._units import (
    BTU_FT2_MIN_TO_W_M2,
    BTU_LB_TO_J_KG,
    FT_INV_TO_M_INV,
    FT_MIN_TO_M_S,
    LB_FT2_TO_KG_M2,
    LB_FT3_TO_KG_M3,
    MPH_TO_M_S,
    btu_ft2_min_to_w_m2,
    btu_lb_to_j_kg,
    feet_to_metres,
    ft_inv_to_m_inv,
    ft_min_to_m_s,
    j_kg_to_btu_lb,
    kg_m2_to_lb_ft2,
    kg_m3_to_lb_ft3,
    lb_ft2_to_kg_m2,
    lb_ft3_to_kg_m3,
    m_inv_to_ft_inv,
    m_s_to_ft_min,
    m_s_to_mph,
    metres_to_feet,
    mph_to_m_s,
    w_m2_to_btu_ft2_min,
)


def test_exact_length_and_spread_rate_conversions() -> None:
    assert feet_to_metres(1.0) == pytest.approx(0.3048)
    assert metres_to_feet(0.3048) == pytest.approx(1.0)
    assert pytest.approx(0.00508) == FT_MIN_TO_M_S
    assert ft_min_to_m_s(1.0) == pytest.approx(0.00508)
    assert m_s_to_ft_min(0.00508) == pytest.approx(1.0)


def test_exact_miles_per_hour_conversion_round_trip() -> None:
    assert pytest.approx(0.44704) == MPH_TO_M_S
    assert mph_to_m_s(1.0) == pytest.approx(0.44704)
    assert m_s_to_mph(0.44704) == pytest.approx(1.0)


def test_fuel_load_conversion_round_trip() -> None:
    assert pytest.approx(4.88242763638305) == LB_FT2_TO_KG_M2
    assert lb_ft2_to_kg_m2(1.0) == pytest.approx(LB_FT2_TO_KG_M2)
    assert kg_m2_to_lb_ft2(LB_FT2_TO_KG_M2) == pytest.approx(1.0)


def test_particle_density_conversion_round_trip() -> None:
    assert pytest.approx(16.0184633739601) == LB_FT3_TO_KG_M3
    assert lb_ft3_to_kg_m3(1.0) == pytest.approx(LB_FT3_TO_KG_M3)
    assert kg_m3_to_lb_ft3(LB_FT3_TO_KG_M3) == pytest.approx(1.0)


def test_surface_area_to_volume_conversion_round_trip() -> None:
    assert pytest.approx(3.28083989501312) == FT_INV_TO_M_INV
    assert ft_inv_to_m_inv(1.0) == pytest.approx(FT_INV_TO_M_INV)
    assert m_inv_to_ft_inv(FT_INV_TO_M_INV) == pytest.approx(1.0)


def test_heat_content_conversion_round_trip() -> None:
    assert pytest.approx(2326.0, rel=1e-5) == BTU_LB_TO_J_KG
    assert btu_lb_to_j_kg(1.0) == pytest.approx(BTU_LB_TO_J_KG)
    assert j_kg_to_btu_lb(BTU_LB_TO_J_KG) == pytest.approx(1.0)


def test_reaction_intensity_conversion_round_trip() -> None:
    assert pytest.approx(189.2754447037829, rel=1e-14) == BTU_FT2_MIN_TO_W_M2
    assert btu_ft2_min_to_w_m2(1.0) == pytest.approx(BTU_FT2_MIN_TO_W_M2)
    assert w_m2_to_btu_ft2_min(BTU_FT2_MIN_TO_W_M2) == pytest.approx(1.0)


def test_conversion_helpers_preserve_zero() -> None:
    assert feet_to_metres(0.0) == 0.0
    assert lb_ft2_to_kg_m2(0.0) == 0.0
    assert lb_ft3_to_kg_m3(0.0) == 0.0
    assert ft_inv_to_m_inv(0.0) == 0.0
    assert btu_lb_to_j_kg(0.0) == 0.0
    assert btu_ft2_min_to_w_m2(0.0) == 0.0
    assert ft_min_to_m_s(0.0) == 0.0
    assert mph_to_m_s(0.0) == 0.0
