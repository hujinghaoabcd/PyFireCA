import pytest

from pyfireca.behavior._rothermel_dynamic import (
    apply_dynamic_herbaceous_transfer,
    compute_dynamic_herbaceous_transfer_fraction,
)
from pyfireca.behavior.rothermel import (
    FuelClass,
    RothermelFuelModel,
    RothermelFuelMoisture,
)


def _dynamic_fuel(*, dynamic: bool = True, dead_herb_load: float = 0.0) -> RothermelFuelModel:
    return RothermelFuelModel(
        code=101,
        depth_m=1.0,
        dead_moisture_of_extinction_fraction=0.15,
        loads_kg_m2=(1.0, 0.0, 0.0, dead_herb_load, 3.0, 0.0),
        sav_ratio_m_inv=(1000.0, 100.0, 30.0, 999.0, 2000.0, 1500.0),
        heat_content_j_kg=(10.0, 10.0, 10.0, 11.0, 20.0, 20.0),
        particle_density_kg_m3=(30.0, 30.0, 30.0, 31.0, 40.0, 40.0),
        total_mineral_fraction=(0.05, 0.05, 0.05, 0.06, 0.08, 0.08),
        effective_mineral_fraction=(0.01, 0.01, 0.01, 0.015, 0.02, 0.02),
        dynamic=dynamic,
    )


def _moisture(live_herb: float) -> RothermelFuelMoisture:
    return RothermelFuelMoisture(
        dead_1h_fraction=0.05,
        dead_10h_fraction=0.06,
        dead_100h_fraction=0.07,
        live_herbaceous_fraction=live_herb,
        live_woody_fraction=0.9,
    )


@pytest.mark.parametrize(
    ("moisture", "expected"),
    [
        (0.0, 1.0),
        (0.299, 1.0),
        (0.30, 1.0),
        (0.60, 0.667),
        (1.20, 0.001),
        (1.200001, 0.0),
        (2.0, 0.0),
    ],
)
def test_dynamic_transfer_fraction_matches_pinned_behave_piecewise_rule(
    moisture: float,
    expected: float,
) -> None:
    assert compute_dynamic_herbaceous_transfer_fraction(moisture) == pytest.approx(expected)


def test_dynamic_transfer_conserves_herbaceous_load() -> None:
    original = _dynamic_fuel()
    result = apply_dynamic_herbaceous_transfer(original, _moisture(0.60))
    dead = int(FuelClass.DEAD_HERBACEOUS)
    live = int(FuelClass.LIVE_HERBACEOUS)

    assert result.transfer_fraction == pytest.approx(0.667)
    assert result.transferred_load_kg_m2 == pytest.approx(2.001)
    assert result.fuel.loads_kg_m2[dead] == pytest.approx(2.001)
    assert result.fuel.loads_kg_m2[live] == pytest.approx(0.999)
    assert result.fuel.loads_kg_m2[dead] + result.fuel.loads_kg_m2[live] == pytest.approx(
        original.loads_kg_m2[live]
    )
    assert result.fuel.dynamic is False


def test_transferred_dead_herb_uses_live_sav_but_dead_physical_properties() -> None:
    result = apply_dynamic_herbaceous_transfer(_dynamic_fuel(), _moisture(0.60))
    fuel = result.fuel
    dead = int(FuelClass.DEAD_HERBACEOUS)
    live = int(FuelClass.LIVE_HERBACEOUS)
    dead_1h = int(FuelClass.DEAD_1H)

    assert fuel.sav_ratio_m_inv[dead] == fuel.sav_ratio_m_inv[live]
    assert fuel.heat_content_j_kg[dead] == fuel.heat_content_j_kg[dead_1h]
    assert fuel.particle_density_kg_m3[dead] == fuel.particle_density_kg_m3[dead_1h]
    assert fuel.total_mineral_fraction[dead] == fuel.total_mineral_fraction[dead_1h]
    assert fuel.effective_mineral_fraction[dead] == fuel.effective_mineral_fraction[dead_1h]


def test_moisture_contract_maps_dead_herb_to_dead_one_hour_moisture() -> None:
    values = _moisture(0.60).as_six_class_values()

    assert values[int(FuelClass.DEAD_HERBACEOUS)] == pytest.approx(0.05)
    assert values[int(FuelClass.LIVE_HERBACEOUS)] == pytest.approx(0.60)


def test_static_fuel_is_returned_without_redistribution() -> None:
    fuel = _dynamic_fuel(dynamic=False)
    result = apply_dynamic_herbaceous_transfer(fuel, _moisture(0.60))

    assert result.fuel is fuel
    assert result.transfer_fraction == 0.0
    assert result.transferred_load_kg_m2 == 0.0


def test_dynamic_fuel_rejects_prepopulated_dead_herbaceous_load() -> None:
    with pytest.raises(ValueError, match="zero DEAD_HERBACEOUS"):
        apply_dynamic_herbaceous_transfer(
            _dynamic_fuel(dead_herb_load=0.1),
            _moisture(0.60),
        )


@pytest.mark.parametrize("value", [-0.1, float("inf"), float("nan")])
def test_transfer_fraction_rejects_invalid_moisture(value: float) -> None:
    with pytest.raises(ValueError):
        compute_dynamic_herbaceous_transfer_fraction(value)
