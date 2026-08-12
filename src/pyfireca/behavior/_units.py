"""Exact unit conversions used by fire-behavior reference implementations.

PyFireCA public behavior contracts use SI units. Some published wildfire
behavior equations and reference datasets use US customary units, so the
conversion boundary is centralized and tested rather than repeated inside
scientific formulas.
"""

from __future__ import annotations

FOOT_TO_METRE = 0.3048
POUND_TO_KILOGRAM = 0.45359237
BTU_IT_TO_JOULE = 1055.05585262
MINUTE_TO_SECOND = 60.0

SQUARE_FOOT_TO_SQUARE_METRE = FOOT_TO_METRE**2
CUBIC_FOOT_TO_CUBIC_METRE = FOOT_TO_METRE**3

LB_FT2_TO_KG_M2 = POUND_TO_KILOGRAM / SQUARE_FOOT_TO_SQUARE_METRE
LB_FT3_TO_KG_M3 = POUND_TO_KILOGRAM / CUBIC_FOOT_TO_CUBIC_METRE
BTU_LB_TO_J_KG = BTU_IT_TO_JOULE / POUND_TO_KILOGRAM
FT_INV_TO_M_INV = 1.0 / FOOT_TO_METRE
FT_MIN_TO_M_S = FOOT_TO_METRE / MINUTE_TO_SECOND


def metres_to_feet(value: float) -> float:
    """Convert metres to feet."""

    return value / FOOT_TO_METRE


def feet_to_metres(value: float) -> float:
    """Convert feet to metres."""

    return value * FOOT_TO_METRE


def kg_m2_to_lb_ft2(value: float) -> float:
    """Convert kg/m² to lb/ft²."""

    return value / LB_FT2_TO_KG_M2


def lb_ft2_to_kg_m2(value: float) -> float:
    """Convert lb/ft² to kg/m²."""

    return value * LB_FT2_TO_KG_M2


def kg_m3_to_lb_ft3(value: float) -> float:
    """Convert kg/m³ to lb/ft³."""

    return value / LB_FT3_TO_KG_M3


def lb_ft3_to_kg_m3(value: float) -> float:
    """Convert lb/ft³ to kg/m³."""

    return value * LB_FT3_TO_KG_M3


def m_inv_to_ft_inv(value: float) -> float:
    """Convert inverse metres to inverse feet."""

    return value / FT_INV_TO_M_INV


def ft_inv_to_m_inv(value: float) -> float:
    """Convert inverse feet to inverse metres."""

    return value * FT_INV_TO_M_INV


def j_kg_to_btu_lb(value: float) -> float:
    """Convert J/kg to international-table Btu/lb."""

    return value / BTU_LB_TO_J_KG


def btu_lb_to_j_kg(value: float) -> float:
    """Convert international-table Btu/lb to J/kg."""

    return value * BTU_LB_TO_J_KG


def m_s_to_ft_min(value: float) -> float:
    """Convert m/s to ft/min."""

    return value / FT_MIN_TO_M_S


def ft_min_to_m_s(value: float) -> float:
    """Convert ft/min to m/s."""

    return value * FT_MIN_TO_M_S
