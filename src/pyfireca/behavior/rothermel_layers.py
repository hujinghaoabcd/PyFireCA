"""Static raster-layer adapter for spatially heterogeneous Rothermel inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

import numpy as np
from numpy.typing import NDArray

from pyfireca.behavior.fuel_catalog import get_standard_fuel_model
from pyfireca.behavior.rothermel import (
    RothermelFuelModel,
    RothermelFuelMoisture,
    RothermelInputs,
)
from pyfireca.data import EnvironmentalData, MissingEnvironmentalDataError, nodata_mask

BooleanMask = NDArray[np.bool_]


@dataclass(frozen=True, slots=True)
class RothermelRasterLayerNames:
    """Names of static environmental layers required by Rothermel."""

    fuel_model: str = "fuel_model"
    dead_1h_moisture: str = "dead_1h_moisture"
    dead_10h_moisture: str = "dead_10h_moisture"
    dead_100h_moisture: str = "dead_100h_moisture"
    live_herbaceous_moisture: str = "live_herbaceous_moisture"
    live_woody_moisture: str = "live_woody_moisture"
    midflame_wind_speed: str = "midflame_wind_speed"
    wind_from_direction: str = "wind_from_direction"
    slope: str = "slope"
    aspect: str = "aspect"

    def ordered(self) -> tuple[str, ...]:
        """Return layer names in one deterministic validation order."""

        return (
            self.fuel_model,
            self.dead_1h_moisture,
            self.dead_10h_moisture,
            self.dead_100h_moisture,
            self.live_herbaceous_moisture,
            self.live_woody_moisture,
            self.midflame_wind_speed,
            self.wind_from_direction,
            self.slope,
            self.aspect,
        )


@dataclass(slots=True)
class StaticRasterRothermelInputsProvider:
    """Build one typed :class:`RothermelInputs` from aligned static raster layers.

    Only cells inside ``domain_mask`` are required to contain complete behavior
    inputs. This preserves the GIS contract that NoData outside the simulation
    domain is legitimate. Every required layer must be static and already use
    the exact units expected by :class:`RothermelInputs`; this adapter never
    performs hidden percentage, wind-height, slope, or angular conversions.
    """

    environment: EnvironmentalData
    domain_mask: BooleanMask
    names: RothermelRasterLayerNames = field(default_factory=RothermelRasterLayerNames)
    _arrays: dict[str, NDArray[np.number]] = field(init=False, repr=False)
    _fuel_models: dict[int, RothermelFuelModel] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.environment, EnvironmentalData):
            raise TypeError("environment must be EnvironmentalData")
        if not isinstance(self.names, RothermelRasterLayerNames):
            raise TypeError("names must be RothermelRasterLayerNames")

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
                    f"layer {name!r} is dynamic; StaticRasterRothermelInputsProvider "
                    "accepts static layers only"
                )
            values = layer.at()
            missing = nodata_mask(layer) | ~np.isfinite(values)
            invalid_inside = missing & domain
            if np.any(invalid_inside):
                count = int(np.count_nonzero(invalid_inside))
                raise MissingEnvironmentalDataError(
                    f"required static Rothermel layer {name!r} has {count} unusable "
                    "cells inside the simulation domain"
                )
            arrays[name] = values

        self._validate_units()
        self._arrays = arrays
        self._fuel_models = self._resolve_fuel_models(arrays[self.names.fuel_model], domain)

    def _validate_units(self) -> None:
        expected = {
            self.names.dead_1h_moisture: "fraction",
            self.names.dead_10h_moisture: "fraction",
            self.names.dead_100h_moisture: "fraction",
            self.names.live_herbaceous_moisture: "fraction",
            self.names.live_woody_moisture: "fraction",
            self.names.midflame_wind_speed: "m/s",
            self.names.wind_from_direction: "deg",
            self.names.slope: "deg",
            self.names.aspect: "deg",
        }
        for name, unit in expected.items():
            actual = self.environment.layer(name).units
            if actual != unit:
                raise ValueError(
                    f"layer {name!r} must declare units={unit!r}; got {actual!r}"
                )

        fuel_units = self.environment.layer(self.names.fuel_model).units
        if fuel_units not in (None, "code"):
            raise ValueError(
                f"fuel-model layer must use units=None or 'code'; got {fuel_units!r}"
            )

    @staticmethod
    def _resolve_fuel_models(
        fuel_values: NDArray[np.number],
        domain: BooleanMask,
    ) -> dict[int, RothermelFuelModel]:
        models: dict[int, RothermelFuelModel] = {}
        for raw in np.unique(fuel_values[domain]):
            value = float(raw)
            if not isfinite(value) or not value.is_integer():
                raise ValueError(
                    f"fuel-model codes inside the simulation domain must be integers; got {raw!r}"
                )
            code = int(value)
            models[code] = get_standard_fuel_model(code)
        return models

    def __call__(self, row: int, col: int) -> RothermelInputs:
        """Return typed behavior inputs for one in-domain source cell."""

        if isinstance(row, bool) or isinstance(col, bool) or not isinstance(row, int) or not isinstance(col, int):
            raise TypeError("row and col must be integers")
        rows, cols = self.environment.spatial_shape
        if not 0 <= row < rows or not 0 <= col < cols:
            raise IndexError(f"cell ({row}, {col}) is outside environment shape {(rows, cols)}")
        if not bool(self.domain_mask[row, col]):
            raise ValueError(f"cell ({row}, {col}) is outside the simulation domain")

        arrays = self._arrays
        fuel_code = int(float(arrays[self.names.fuel_model][row, col]))
        moisture = RothermelFuelMoisture(
            dead_1h_fraction=float(arrays[self.names.dead_1h_moisture][row, col]),
            dead_10h_fraction=float(arrays[self.names.dead_10h_moisture][row, col]),
            dead_100h_fraction=float(arrays[self.names.dead_100h_moisture][row, col]),
            live_herbaceous_fraction=float(
                arrays[self.names.live_herbaceous_moisture][row, col]
            ),
            live_woody_fraction=float(arrays[self.names.live_woody_moisture][row, col]),
        )
        return RothermelInputs(
            fuel=self._fuel_models[fuel_code],
            moisture=moisture,
            midflame_wind_speed_m_s=float(
                arrays[self.names.midflame_wind_speed][row, col]
            ),
            wind_from_direction_deg=float(
                arrays[self.names.wind_from_direction][row, col]
            ),
            slope_deg=float(arrays[self.names.slope][row, col]),
            aspect_deg=float(arrays[self.names.aspect][row, col]),
        )
