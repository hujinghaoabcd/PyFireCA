import pytest

from pyfireca.behavior.rothermel import (
    FuelClass,
    RothermelFuelModel,
    RothermelFuelMoisture,
    RothermelInputs,
)


def _valid_fuel_model() -> RothermelFuelModel:
    return RothermelFuelModel(
        code=1,
        depth_m=0.30,
        dead_moisture_of_extinction_fraction=0.12,
        loads_kg_m2=(0.20, 0.05, 0.01, 0.0, 0.08, 0.02),
        sav_ratio_m_inv=(5000.0, 360.0, 100.0, 0.0, 4500.0, 4000.0),
        heat_content_j_kg=(
            18_600_000.0,
            18_600_000.0,
            18_600_000.0,
            0.0,
            18_600_000.0,
            18_600_000.0,
        ),
        particle_density_kg_m3=(
            512.0,
            512.0,
            512.0,
            0.0,
            512.0,
            512.0,
        ),
        total_mineral_fraction=(0.0555, 0.0555, 0.0555, 0.0, 0.0555, 0.0555),
        effective_mineral_fraction=(0.01, 0.01, 0.01, 0.0, 0.01, 0.01),
    )


def test_fuel_class_order_is_explicit_and_stable() -> None:
    assert tuple(FuelClass) == (
        FuelClass.DEAD_1H,
        FuelClass.DEAD_10H,
        FuelClass.DEAD_100H,
        FuelClass.DEAD_HERBACEOUS,
        FuelClass.LIVE_HERBACEOUS,
        FuelClass.LIVE_WOODY,
    )
    assert [int(value) for value in FuelClass] == list(range(6))


def test_valid_burnable_fuel_model_preserves_six_class_values() -> None:
    fuel = _valid_fuel_model()

    assert fuel.burnable
    assert fuel.loads_kg_m2[FuelClass.DEAD_1H] == 0.20
    assert fuel.loads_kg_m2[FuelClass.LIVE_WOODY] == 0.02


def test_burnable_fuel_requires_positive_depth_extinction_and_load() -> None:
    common = dict(
        code=1,
        loads_kg_m2=(0.2, 0.0, 0.0, 0.0, 0.0, 0.0),
        sav_ratio_m_inv=(5000.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        heat_content_j_kg=(18_600_000.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        particle_density_kg_m3=(512.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        total_mineral_fraction=(0.0555, 0.0, 0.0, 0.0, 0.0, 0.0),
        effective_mineral_fraction=(0.01, 0.0, 0.0, 0.0, 0.0, 0.0),
    )

    with pytest.raises(ValueError, match="positive depth"):
        RothermelFuelModel(
            depth_m=0.0,
            dead_moisture_of_extinction_fraction=0.12,
            **common,
        )

    with pytest.raises(ValueError, match="moisture of extinction"):
        RothermelFuelModel(
            depth_m=0.30,
            dead_moisture_of_extinction_fraction=0.0,
            **common,
        )

    with pytest.raises(ValueError, match="positive total fuel load"):
        RothermelFuelModel(
            code=2,
            depth_m=0.30,
            dead_moisture_of_extinction_fraction=0.12,
            loads_kg_m2=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            sav_ratio_m_inv=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            heat_content_j_kg=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            particle_density_kg_m3=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            total_mineral_fraction=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            effective_mineral_fraction=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )


def test_loaded_class_requires_positive_physical_properties() -> None:
    fuel = _valid_fuel_model()
    values = list(fuel.sav_ratio_m_inv)
    values[FuelClass.DEAD_1H] = 0.0

    with pytest.raises(ValueError, match="positive SAV"):
        RothermelFuelModel(
            code=fuel.code,
            depth_m=fuel.depth_m,
            dead_moisture_of_extinction_fraction=fuel.dead_moisture_of_extinction_fraction,
            loads_kg_m2=fuel.loads_kg_m2,
            sav_ratio_m_inv=tuple(values),  # type: ignore[arg-type]
            heat_content_j_kg=fuel.heat_content_j_kg,
            particle_density_kg_m3=fuel.particle_density_kg_m3,
            total_mineral_fraction=fuel.total_mineral_fraction,
            effective_mineral_fraction=fuel.effective_mineral_fraction,
        )


def test_nonburnable_zero_fuel_model_is_allowed() -> None:
    zeros = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    fuel = RothermelFuelModel(
        code=91,
        depth_m=0.0,
        dead_moisture_of_extinction_fraction=0.0,
        loads_kg_m2=zeros,
        sav_ratio_m_inv=zeros,
        heat_content_j_kg=zeros,
        particle_density_kg_m3=zeros,
        total_mineral_fraction=zeros,
        effective_mineral_fraction=zeros,
        burnable=False,
    )

    assert not fuel.burnable


def test_six_class_fields_reject_wrong_length_and_invalid_fraction() -> None:
    fuel = _valid_fuel_model()

    with pytest.raises(ValueError, match="exactly six"):
        RothermelFuelModel(
            code=1,
            depth_m=fuel.depth_m,
            dead_moisture_of_extinction_fraction=0.12,
            loads_kg_m2=(0.2, 0.0),  # type: ignore[arg-type]
            sav_ratio_m_inv=fuel.sav_ratio_m_inv,
            heat_content_j_kg=fuel.heat_content_j_kg,
            particle_density_kg_m3=fuel.particle_density_kg_m3,
            total_mineral_fraction=fuel.total_mineral_fraction,
            effective_mineral_fraction=fuel.effective_mineral_fraction,
        )

    mineral = list(fuel.total_mineral_fraction)
    mineral[FuelClass.DEAD_1H] = 1.1
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        RothermelFuelModel(
            code=1,
            depth_m=fuel.depth_m,
            dead_moisture_of_extinction_fraction=0.12,
            loads_kg_m2=fuel.loads_kg_m2,
            sav_ratio_m_inv=fuel.sav_ratio_m_inv,
            heat_content_j_kg=fuel.heat_content_j_kg,
            particle_density_kg_m3=fuel.particle_density_kg_m3,
            total_mineral_fraction=tuple(mineral),  # type: ignore[arg-type]
            effective_mineral_fraction=fuel.effective_mineral_fraction,
        )


def test_fuel_moisture_expands_to_six_class_order() -> None:
    moisture = RothermelFuelMoisture(
        dead_1h_fraction=0.05,
        dead_10h_fraction=0.07,
        dead_100h_fraction=0.09,
        live_herbaceous_fraction=1.20,
        live_woody_fraction=0.90,
    )

    assert moisture.as_six_class_values() == (0.05, 0.07, 0.09, 0.05, 1.20, 0.90)


def test_fuel_moisture_allows_live_values_above_one_but_not_negative() -> None:
    RothermelFuelMoisture(0.05, 0.07, 0.09, 1.50, 1.10)

    with pytest.raises(ValueError, match="non-negative"):
        RothermelFuelMoisture(0.05, 0.07, 0.09, -0.01, 1.10)


def test_rothermel_inputs_validate_wind_slope_and_directions() -> None:
    fuel = _valid_fuel_model()
    moisture = RothermelFuelMoisture(0.05, 0.07, 0.09, 1.20, 0.90)

    inputs = RothermelInputs(
        fuel=fuel,
        moisture=moisture,
        midflame_wind_speed_m_s=4.0,
        wind_from_direction_deg=270.0,
        slope_deg=15.0,
        aspect_deg=180.0,
    )
    assert inputs.midflame_wind_speed_m_s == 4.0

    with pytest.raises(ValueError, match="wind_from_direction_deg"):
        RothermelInputs(fuel, moisture, 4.0, 360.0, 15.0, 180.0)

    with pytest.raises(ValueError, match="slope_deg"):
        RothermelInputs(fuel, moisture, 4.0, 270.0, 90.0, 180.0)

    with pytest.raises(ValueError, match="non-negative"):
        RothermelInputs(fuel, moisture, -1.0, 270.0, 15.0, 180.0)
