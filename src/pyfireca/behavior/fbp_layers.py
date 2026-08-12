"""Static raster-layer adapter for spatially heterogeneous Canadian FBP inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

import numpy as np
from numpy.typing import NDArray

from pyfireca.behavior.fbp import FBPInputs
from pyfireca.data import EnvironmentalData, MissingEnvironmentalDataError, nodata_mask

BooleanMask = NDArray[np.bool_]

_FBP_NUMERIC_FUEL_CODES = {
    1: "C1",
    2: "C2",
    3: "C3",
    4: "C4",
    5: "C5",
    6: "C6",
    7: "C7",
    8: "D1",
    9: "D2",
    10: "M1",
    11: "M2",
    12: "M3",
    13: "M4",
    14: "O1A",
    15: "O1B",
    16: "S1",
    17: "S2",
    18: "S3",
    19: "NF",
    20: "WA",
}


@dataclass(frozen=True, slots=True)
class FBPRasterLayerNames:
    """Names of static environmental layers required by Canadian FBP."""

    fuel_type: str = "fbp_fuel_type"
    ffmc: str = "ffmc"
    bui: str = "bui"
    wind_speed_10m: str = "wind_speed_10m"
    wind_from_direction: str = "wind_from_direction"
    slope_percent: str = "slope_percent"
    aspect: str = "aspect"
    latitude: str = "latitude"
    longitude: str = "longitude"
    elevation: str = "elevation"

    def ordered(self) -> tuple[str, ...]:
        """Return layer names in deterministic validation order."""

        return (
            self.fuel_type,
            self.ffmc,
            self.bui,
            self.wind_speed_10m,
            self.wind_from_direction,
            self.slope_percent,
            self.aspect,
            self.latitude,
            self.longitude,
            self.elevation,
        )


@dataclass(slots=True)
class StaticRasterFBPInputsProvider:
    """Build one :class:`FBPInputs` from aligned static raster layers.

    FBP uses its native data contract: FFMC/BUI, 10-m wind and slope percent.
    The adapter performs no hidden conversion from Rothermel inputs. Mixedwood
    and grass parameters are explicit scalar defaults for this first static
    raster adapter and can be promoted to raster layers later if required.
    """

    environment: EnvironmentalData
    domain_mask: BooleanMask
    julian_day: int
    names: FBPRasterLayerNames = field(default_factory=FBPRasterLayerNames)
    percent_conifer: float = 50.0
    percent_dead_fir: float = 35.0
    grass_fuel_load_kg_m2: float = 0.35
    grass_curing_percent: float = 80.0
    day_of_minimum_foliar_moisture: int | None = None
    _arrays: dict[str, NDArray[np.number]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.environment, EnvironmentalData):
            raise TypeError("environment must be EnvironmentalData")
        if not isinstance(self.names, FBPRasterLayerNames):
            raise TypeError("names must be FBPRasterLayerNames")
        if isinstance(self.julian_day, bool) or not isinstance(self.julian_day, int):
            raise TypeError("julian_day must be an integer")
        if not 1 <= self.julian_day <= 366:
            raise ValueError("julian_day must be in [1, 366]")

        domain = np.asarray(self.domain_mask)
        if domain.dtype != np.bool_:
            raise TypeError("domain_mask must use a boolean dtype")
        if domain.shape != self.environment.spatial_shape:
            raise ValueError(
                f"domain_mask shape {domain.shape} does not match environment shape "
                f"{self.environment.spatial_shape}"
            )
        self.domain_mask = domain

        arrays: dict[str, NDArray[np.number]] = {}
        for name in self.names.ordered():
            layer = self.environment.layer(name)
            if layer.is_dynamic:
                raise ValueError(
                    f"layer {name!r} is dynamic; StaticRasterFBPInputsProvider "
                    "accepts static layers only"
                )
            values = layer.at()
            missing = nodata_mask(layer) | ~np.isfinite(values)
            invalid_inside = missing & domain
            if np.any(invalid_inside):
                count = int(np.count_nonzero(invalid_inside))
                raise MissingEnvironmentalDataError(
                    f"required static FBP layer {name!r} has {count} unusable "
                    "cells inside the simulation domain"
                )
            arrays[name] = values

        self._validate_units()
        self._validate_fuel_codes(arrays[self.names.fuel_type], domain)
        self._arrays = arrays

        # Validate scalar optional inputs through the same FBPInputs contract.
        samples = np.argwhere(domain)
        if samples.size:
            row, col = (int(value) for value in samples[0])
            self(row, col)

    def _validate_units(self) -> None:
        expected = {
            self.names.ffmc: "code",
            self.names.bui: "index",
            self.names.wind_speed_10m: "km/h",
            self.names.wind_from_direction: "deg",
            self.names.slope_percent: "percent",
            self.names.aspect: "deg",
            self.names.latitude: "deg",
            self.names.longitude: "deg",
            self.names.elevation: "m",
        }
        for name, unit in expected.items():
            actual = self.environment.layer(name).units
            if actual != unit:
                raise ValueError(f"layer {name!r} must declare units={unit!r}; got {actual!r}")

        fuel_units = self.environment.layer(self.names.fuel_type).units
        if fuel_units not in (None, "code"):
            raise ValueError(f"FBP fuel-type layer must use units=None or 'code'; got {fuel_units!r}")

    @staticmethod
    def _validate_fuel_codes(
        fuel_values: NDArray[np.number],
        domain: BooleanMask,
    ) -> None:
        for raw in np.unique(fuel_values[domain]):
            value = float(raw)
            if not isfinite(value) or not value.is_integer():
                raise ValueError(
                    f"FBP fuel-type codes inside the simulation domain must be integers; got {raw!r}"
                )
            code = int(value)
            if code not in _FBP_NUMERIC_FUEL_CODES:
                raise ValueError(f"unsupported numeric FBP fuel-type code {code}; expected 1..20")
            if code in (19, 20):
                raise ValueError(
                    "FBP NF/WA cells must be marked UNBURNABLE in landscape.initial_state"
                )

    def __call__(self, row: int, col: int) -> FBPInputs:
        """Return typed FBP behavior inputs for one in-domain source cell."""

        if (
            isinstance(row, bool)
            or isinstance(col, bool)
            or not isinstance(row, int)
            or not isinstance(col, int)
        ):
            raise TypeError("row and col must be integers")
        rows, cols = self.environment.spatial_shape
        if not 0 <= row < rows or not 0 <= col < cols:
            raise IndexError(f"cell ({row}, {col}) is outside environment shape {(rows, cols)}")
        if not bool(self.domain_mask[row, col]):
            raise ValueError(f"cell ({row}, {col}) is outside the simulation domain")

        arrays = self._arrays
        fuel_code = int(float(arrays[self.names.fuel_type][row, col]))
        return FBPInputs(
            fuel_type=_FBP_NUMERIC_FUEL_CODES[fuel_code],
            ffmc=float(arrays[self.names.ffmc][row, col]),
            bui=float(arrays[self.names.bui][row, col]),
            wind_speed_10m_kmh=float(arrays[self.names.wind_speed_10m][row, col]),
            wind_from_direction_deg=float(arrays[self.names.wind_from_direction][row, col]),
            slope_percent=float(arrays[self.names.slope_percent][row, col]),
            aspect_deg=float(arrays[self.names.aspect][row, col]),
            latitude_deg=float(arrays[self.names.latitude][row, col]),
            longitude_deg=float(arrays[self.names.longitude][row, col]),
            elevation_m=float(arrays[self.names.elevation][row, col]),
            julian_day=self.julian_day,
            percent_conifer=self.percent_conifer,
            percent_dead_fir=self.percent_dead_fir,
            grass_fuel_load_kg_m2=self.grass_fuel_load_kg_m2,
            grass_curing_percent=self.grass_curing_percent,
            day_of_minimum_foliar_moisture=self.day_of_minimum_foliar_moisture,
        )
