"""Tests for the self-contained Van Wagner/Cruz crown-fire implementation."""

import pytest

from pyfireca.behavior.crown import (
    CrownFireType,
    CruzCrownFireModel,
    CruzCrownInputs,
    cruz_active_crown_ros_m_min,
    cruz_passive_crown_ros_m_min,
    van_wagner_critical_crown_ros_m_min,
    van_wagner_critical_fireline_intensity_w_m,
)


def test_van_wagner_critical_intensity_reference_equation():
    value = van_wagner_critical_fireline_intensity_w_m(3.0, 1.0)
    assert value == pytest.approx(879557.0658007358)


def test_cruz_active_and_passive_rates_are_self_contained():
    active = cruz_active_crown_ros_m_min(30.0, 0.15, 0.06)
    critical = van_wagner_critical_crown_ros_m_min(0.15)
    passive = cruz_passive_crown_ros_m_min(active, critical)
    assert active == pytest.approx(59.16538452972305)
    assert critical == pytest.approx(20.0)
    assert passive == pytest.approx(3.0711971097005297)


def test_crown_model_returns_no_crown_below_initiation_threshold():
    result = CruzCrownFireModel().compute(
        CruzCrownInputs(
            surface_fireline_intensity_w_m=1000.0,
            canopy_cover_fraction=0.8,
            canopy_base_height_m=3.0,
            canopy_height_m=15.0,
            canopy_bulk_density_kg_m3=0.15,
            foliar_moisture_fraction=1.0,
            fine_fuel_moisture_fraction=0.06,
            wind_speed_10m_kmh=30.0,
            downwind_direction_deg=180.0,
        )
    )
    assert result.spread_rate_m_s == 0.0
    assert result.diagnostics["fire_type"] == float(CrownFireType.NONE)


def test_crown_model_returns_active_crown_when_thresholds_are_met():
    critical_intensity = van_wagner_critical_fireline_intensity_w_m(3.0, 1.0)
    result = CruzCrownFireModel().compute(
        CruzCrownInputs(
            surface_fireline_intensity_w_m=critical_intensity * 1.1,
            canopy_cover_fraction=0.8,
            canopy_base_height_m=3.0,
            canopy_height_m=15.0,
            canopy_bulk_density_kg_m3=0.15,
            foliar_moisture_fraction=1.0,
            fine_fuel_moisture_fraction=0.06,
            wind_speed_10m_kmh=30.0,
            downwind_direction_deg=180.0,
        )
    )
    assert result.diagnostics["fire_type"] == float(CrownFireType.ACTIVE)
    assert result.spread_rate_m_s == pytest.approx(59.16538452972305 / 60.0)
    assert result.fireline_intensity_w_m > 0.0
