"""Auditable standard fuel-model catalogue entries for Rothermel behavior.

Anderson 13 records and the currently validated Scott--Burgan subset are taken
from one pinned USFS Fire Lab Behave core revision. Additional Scott--Burgan
records should be added from the same pinned source rather than copied from
secondary tables.
"""

from __future__ import annotations

from dataclasses import dataclass

from pyfireca.behavior._units import (
    btu_lb_to_j_kg,
    feet_to_metres,
    ft_inv_to_m_inv,
    lb_ft2_to_kg_m2,
    lb_ft3_to_kg_m3,
)
from pyfireca.behavior.rothermel import RothermelFuelModel

_PINNED_BEHAVE_CORE_COMMIT = "29888c7ad364aa18cfb340f4c25a8e395f24260f"
_TON_ACRE_TO_LB_FT2 = 2000.0 / 43560.0
_STANDARD_PARTICLE_DENSITY_LB_FT3 = 32.0
_STANDARD_TOTAL_MINERAL_FRACTION = 0.0555
_STANDARD_EFFECTIVE_MINERAL_FRACTION = 0.01
_DEAD_10H_SAV_FT_INV = 109.0
_DEAD_100H_SAV_FT_INV = 30.0


@dataclass(frozen=True, slots=True)
class StandardFuelModelRecord:
    """One pinned Behave standard-fuel record in native catalogue units."""

    number: int
    code: str
    description: str
    depth_ft: float
    dead_moisture_of_extinction_fraction: float
    dead_heat_btu_lb: float
    live_heat_btu_lb: float
    dead_1h_load_lb_ft2: float
    dead_10h_load_lb_ft2: float
    dead_100h_load_lb_ft2: float
    live_herbaceous_load_lb_ft2: float
    live_woody_load_lb_ft2: float
    dead_1h_sav_ft_inv: float
    live_herbaceous_sav_ft_inv: float
    live_woody_sav_ft_inv: float
    dynamic: bool

    @property
    def source_commit(self) -> str:
        """Return the pinned Behave core revision used for this record."""

        return _PINNED_BEHAVE_CORE_COMMIT

    def to_rothermel_fuel_model(self) -> RothermelFuelModel:
        """Convert the native catalogue record into PyFireCA's SI contract."""

        dead_heat = btu_lb_to_j_kg(self.dead_heat_btu_lb)
        live_heat = btu_lb_to_j_kg(self.live_heat_btu_lb)
        density = lb_ft3_to_kg_m3(_STANDARD_PARTICLE_DENSITY_LB_FT3)

        return RothermelFuelModel(
            code=self.number,
            depth_m=feet_to_metres(self.depth_ft),
            dead_moisture_of_extinction_fraction=(self.dead_moisture_of_extinction_fraction),
            loads_kg_m2=(
                lb_ft2_to_kg_m2(self.dead_1h_load_lb_ft2),
                lb_ft2_to_kg_m2(self.dead_10h_load_lb_ft2),
                lb_ft2_to_kg_m2(self.dead_100h_load_lb_ft2),
                0.0,
                lb_ft2_to_kg_m2(self.live_herbaceous_load_lb_ft2),
                lb_ft2_to_kg_m2(self.live_woody_load_lb_ft2),
            ),
            sav_ratio_m_inv=(
                ft_inv_to_m_inv(self.dead_1h_sav_ft_inv),
                ft_inv_to_m_inv(_DEAD_10H_SAV_FT_INV),
                ft_inv_to_m_inv(_DEAD_100H_SAV_FT_INV),
                0.0,
                ft_inv_to_m_inv(self.live_herbaceous_sav_ft_inv),
                ft_inv_to_m_inv(self.live_woody_sav_ft_inv),
            ),
            heat_content_j_kg=(
                dead_heat,
                dead_heat,
                dead_heat,
                0.0,
                live_heat,
                live_heat,
            ),
            particle_density_kg_m3=(density, density, density, 0.0, density, density),
            total_mineral_fraction=(
                _STANDARD_TOTAL_MINERAL_FRACTION,
                _STANDARD_TOTAL_MINERAL_FRACTION,
                _STANDARD_TOTAL_MINERAL_FRACTION,
                0.0,
                _STANDARD_TOTAL_MINERAL_FRACTION,
                _STANDARD_TOTAL_MINERAL_FRACTION,
            ),
            effective_mineral_fraction=(
                _STANDARD_EFFECTIVE_MINERAL_FRACTION,
                _STANDARD_EFFECTIVE_MINERAL_FRACTION,
                _STANDARD_EFFECTIVE_MINERAL_FRACTION,
                0.0,
                _STANDARD_EFFECTIVE_MINERAL_FRACTION,
                _STANDARD_EFFECTIVE_MINERAL_FRACTION,
            ),
            dynamic=self.dynamic,
        )


_VERIFIED_STANDARD_FUEL_MODELS: dict[int, StandardFuelModelRecord] = {
    1: StandardFuelModelRecord(
        number=1,
        code="FM1",
        description="Short grass [1]",
        depth_ft=1.0,
        dead_moisture_of_extinction_fraction=0.12,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.034,
        dead_10h_load_lb_ft2=0.0,
        dead_100h_load_lb_ft2=0.0,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=3500.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    2: StandardFuelModelRecord(
        number=2,
        code="FM2",
        description="Timber grass and understory [2]",
        depth_ft=1.0,
        dead_moisture_of_extinction_fraction=0.15,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.092,
        dead_10h_load_lb_ft2=0.046,
        dead_100h_load_lb_ft2=0.023,
        live_herbaceous_load_lb_ft2=0.023,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=3000.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    3: StandardFuelModelRecord(
        number=3,
        code="FM3",
        description="Tall grass [3]",
        depth_ft=2.5,
        dead_moisture_of_extinction_fraction=0.25,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.138,
        dead_10h_load_lb_ft2=0.0,
        dead_100h_load_lb_ft2=0.0,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=1500.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    4: StandardFuelModelRecord(
        number=4,
        code="FM4",
        description="Chaparral [4]",
        depth_ft=6.0,
        dead_moisture_of_extinction_fraction=0.20,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.230,
        dead_10h_load_lb_ft2=0.184,
        dead_100h_load_lb_ft2=0.092,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.230,
        dead_1h_sav_ft_inv=2000.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    5: StandardFuelModelRecord(
        number=5,
        code="FM5",
        description="Brush [5]",
        depth_ft=2.0,
        dead_moisture_of_extinction_fraction=0.20,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.046,
        dead_10h_load_lb_ft2=0.023,
        dead_100h_load_lb_ft2=0.0,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.092,
        dead_1h_sav_ft_inv=2000.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    6: StandardFuelModelRecord(
        number=6,
        code="FM6",
        description="Dormant brush, hardwood slash [6]",
        depth_ft=2.5,
        dead_moisture_of_extinction_fraction=0.25,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.069,
        dead_10h_load_lb_ft2=0.115,
        dead_100h_load_lb_ft2=0.092,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=1750.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    7: StandardFuelModelRecord(
        number=7,
        code="FM7",
        description="Southern rough [7]",
        depth_ft=2.5,
        dead_moisture_of_extinction_fraction=0.40,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.052,
        dead_10h_load_lb_ft2=0.086,
        dead_100h_load_lb_ft2=0.069,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.017,
        dead_1h_sav_ft_inv=1750.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    8: StandardFuelModelRecord(
        number=8,
        code="FM8",
        description="Short needle litter [8]",
        depth_ft=0.2,
        dead_moisture_of_extinction_fraction=0.30,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.069,
        dead_10h_load_lb_ft2=0.046,
        dead_100h_load_lb_ft2=0.115,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=2000.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    9: StandardFuelModelRecord(
        number=9,
        code="FM9",
        description="Long needle or hardwood litter [9]",
        depth_ft=0.2,
        dead_moisture_of_extinction_fraction=0.25,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.134,
        dead_10h_load_lb_ft2=0.019,
        dead_100h_load_lb_ft2=0.007,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=2500.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    10: StandardFuelModelRecord(
        number=10,
        code="FM10",
        description="Timber litter & understory [10]",
        depth_ft=1.0,
        dead_moisture_of_extinction_fraction=0.25,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.138,
        dead_10h_load_lb_ft2=0.092,
        dead_100h_load_lb_ft2=0.230,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.092,
        dead_1h_sav_ft_inv=2000.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    11: StandardFuelModelRecord(
        number=11,
        code="FM11",
        description="Light logging slash [11]",
        depth_ft=1.0,
        dead_moisture_of_extinction_fraction=0.15,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.069,
        dead_10h_load_lb_ft2=0.207,
        dead_100h_load_lb_ft2=0.253,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=1500.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    12: StandardFuelModelRecord(
        number=12,
        code="FM12",
        description="Medium logging slash [12]",
        depth_ft=2.3,
        dead_moisture_of_extinction_fraction=0.20,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.184,
        dead_10h_load_lb_ft2=0.644,
        dead_100h_load_lb_ft2=0.759,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=1500.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    13: StandardFuelModelRecord(
        number=13,
        code="FM13",
        description="Heavy logging slash [13]",
        depth_ft=3.0,
        dead_moisture_of_extinction_fraction=0.25,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.322,
        dead_10h_load_lb_ft2=1.058,
        dead_100h_load_lb_ft2=1.288,
        live_herbaceous_load_lb_ft2=0.0,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=1500.0,
        live_herbaceous_sav_ft_inv=1500.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=False,
    ),
    101: StandardFuelModelRecord(
        number=101,
        code="GR1",
        description="Short, sparse, dry climate grass (D)",
        depth_ft=0.4,
        dead_moisture_of_extinction_fraction=0.15,
        dead_heat_btu_lb=8000.0,
        live_heat_btu_lb=8000.0,
        dead_1h_load_lb_ft2=0.10 * _TON_ACRE_TO_LB_FT2,
        dead_10h_load_lb_ft2=0.0,
        dead_100h_load_lb_ft2=0.0,
        live_herbaceous_load_lb_ft2=0.30 * _TON_ACRE_TO_LB_FT2,
        live_woody_load_lb_ft2=0.0,
        dead_1h_sav_ft_inv=2200.0,
        live_herbaceous_sav_ft_inv=2000.0,
        live_woody_sav_ft_inv=1500.0,
        dynamic=True,
    ),
}


def available_standard_fuel_model_numbers() -> tuple[int, ...]:
    """Return the currently audited standard-fuel model numbers."""

    return tuple(sorted(_VERIFIED_STANDARD_FUEL_MODELS))


def get_standard_fuel_model_record(number: int) -> StandardFuelModelRecord:
    """Return one audited native catalogue record by standard model number."""

    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("number must be an integer fuel-model number")
    try:
        return _VERIFIED_STANDARD_FUEL_MODELS[number]
    except KeyError as exc:
        available = ", ".join(str(value) for value in available_standard_fuel_model_numbers())
        raise KeyError(
            f"standard fuel model {number} has not been audited yet; available: {available}"
        ) from exc


def get_standard_fuel_model(number: int) -> RothermelFuelModel:
    """Return one audited standard fuel model converted to SI units."""

    return get_standard_fuel_model_record(number).to_rothermel_fuel_model()
