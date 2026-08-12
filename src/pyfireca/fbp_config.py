"""Configuration objects for static Canadian FBP wildfire simulations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import yaml

from pyfireca.ignition import IgnitionEvent

_CONFIG_VERSION = 1
_FBP_INPUT_KEYS = (
    "fbp_fuel_type",
    "ffmc",
    "bui",
    "wind_speed_10m",
    "wind_from_direction",
    "slope_percent",
    "aspect",
    "latitude",
    "longitude",
    "elevation",
)
_FBP_BEHAVIOR_KEYS = {
    "model",
    "julian_day",
    "percent_conifer",
    "percent_dead_fir",
    "grass_fuel_load_kg_m2",
    "grass_curing_percent",
    "day_of_minimum_foliar_moisture",
}


@dataclass(frozen=True, slots=True)
class StaticFBPRasterInputPaths:
    """File paths for the ten required static Canadian FBP raster layers."""

    fbp_fuel_type: Path
    ffmc: Path
    bui: Path
    wind_speed_10m: Path
    wind_from_direction: Path
    slope_percent: Path
    aspect: Path
    latitude: Path
    longitude: Path
    elevation: Path

    def __post_init__(self) -> None:
        for name in _FBP_INPUT_KEYS:
            object.__setattr__(self, name, Path(getattr(self, name)))

    def named_paths(self) -> tuple[tuple[str, Path], ...]:
        """Return required FBP raster names and paths in deterministic order."""

        return tuple((name, getattr(self, name)) for name in _FBP_INPUT_KEYS)


@dataclass(frozen=True, slots=True)
class StaticFBPRunConfig:
    """Resolved configuration for one static Canadian FBP simulation."""

    inputs: StaticFBPRasterInputPaths
    cell_size_m: float
    ignitions: tuple[IgnitionEvent, ...]
    output_directory: Path
    julian_day: int
    percent_conifer: float = 50.0
    percent_dead_fir: float = 35.0
    grass_fuel_load_kg_m2: float = 0.35
    grass_curing_percent: float = 80.0
    day_of_minimum_foliar_moisture: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, StaticFBPRasterInputPaths):
            raise TypeError("inputs must be StaticFBPRasterInputPaths")
        if not isfinite(self.cell_size_m) or self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be finite and positive")
        if not self.ignitions or not all(
            isinstance(event, IgnitionEvent) for event in self.ignitions
        ):
            raise ValueError("ignitions must contain at least one IgnitionEvent")
        if isinstance(self.julian_day, bool) or not isinstance(self.julian_day, int):
            raise TypeError("julian_day must be an integer")
        if not 1 <= self.julian_day <= 366:
            raise ValueError("julian_day must be in [1, 366]")
        for name in ("percent_conifer", "percent_dead_fir", "grass_curing_percent"):
            value = float(getattr(self, name))
            if not isfinite(value) or not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be finite and in [0, 100]")
        if not isfinite(self.grass_fuel_load_kg_m2) or self.grass_fuel_load_kg_m2 < 0.0:
            raise ValueError("grass_fuel_load_kg_m2 must be finite and non-negative")
        d0 = self.day_of_minimum_foliar_moisture
        if d0 is not None:
            if isinstance(d0, bool) or not isinstance(d0, int):
                raise TypeError("day_of_minimum_foliar_moisture must be an integer")
            if not 1 <= d0 <= 366:
                raise ValueError("day_of_minimum_foliar_moisture must be in [1, 366]")
        object.__setattr__(self, "output_directory", Path(self.output_directory))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serializable resolved FBP configuration."""

        behavior: dict[str, object] = {
            "model": "fbp",
            "julian_day": self.julian_day,
            "percent_conifer": self.percent_conifer,
            "percent_dead_fir": self.percent_dead_fir,
            "grass_fuel_load_kg_m2": self.grass_fuel_load_kg_m2,
            "grass_curing_percent": self.grass_curing_percent,
        }
        if self.day_of_minimum_foliar_moisture is not None:
            behavior["day_of_minimum_foliar_moisture"] = self.day_of_minimum_foliar_moisture
        return {
            "version": _CONFIG_VERSION,
            "behavior": behavior,
            "cell_size_m": self.cell_size_m,
            "inputs": {name: str(path) for name, path in self.inputs.named_paths()},
            "ignitions": [
                {"row": event.row, "col": event.col, "time_s": event.time_s}
                for event in self.ignitions
            ],
            "output": {"directory": str(self.output_directory)},
        }


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _path(value: object, *, base: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty path string")
    result = Path(value).expanduser()
    if not result.is_absolute():
        result = base / result
    return result.resolve()


def _number(mapping: Mapping[str, object], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"behavior.{key} must be numeric")
    return float(value)


def load_static_fbp_run_config(path: str | Path) -> StaticFBPRunConfig:
    """Load and strictly validate one version-1 Canadian FBP YAML config."""

    config_path = Path(path).expanduser().resolve()
    root = _mapping(yaml.safe_load(config_path.read_text(encoding="utf-8")), "configuration")
    allowed_root = {"version", "behavior", "cell_size_m", "inputs", "ignitions", "output"}
    unknown_root = set(root) - allowed_root
    if unknown_root:
        raise ValueError(f"unknown configuration keys: {sorted(unknown_root)}")
    if root.get("version") != _CONFIG_VERSION:
        raise ValueError(f"configuration version must be {_CONFIG_VERSION}")

    behavior = _mapping(root.get("behavior"), "behavior")
    unknown_behavior = set(behavior) - _FBP_BEHAVIOR_KEYS
    if unknown_behavior:
        raise ValueError(f"unknown FBP behavior keys: {sorted(unknown_behavior)}")
    if behavior.get("model") != "fbp":
        raise ValueError("behavior.model must be 'fbp' for an FBP configuration")
    julian_day = behavior.get("julian_day")
    if isinstance(julian_day, bool) or not isinstance(julian_day, int):
        raise ValueError("behavior.julian_day must be an integer")

    base = config_path.parent
    raw_inputs = _mapping(root.get("inputs"), "inputs")
    missing = set(_FBP_INPUT_KEYS) - set(raw_inputs)
    unknown = set(raw_inputs) - set(_FBP_INPUT_KEYS)
    if missing:
        raise ValueError(f"missing required FBP input rasters: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown FBP input raster keys: {sorted(unknown)}")
    input_kwargs = {
        name: _path(raw_inputs[name], base=base, label=f"inputs.{name}")
        for name in _FBP_INPUT_KEYS
    }
    inputs = StaticFBPRasterInputPaths(**input_kwargs)

    raw_ignitions = root.get("ignitions")
    if not isinstance(raw_ignitions, list) or not raw_ignitions:
        raise ValueError("ignitions must be a non-empty list")
    ignitions: list[IgnitionEvent] = []
    for index, raw_event in enumerate(raw_ignitions):
        event = _mapping(raw_event, f"ignitions[{index}]")
        unknown_event = set(event) - {"row", "col", "time_s"}
        if unknown_event:
            raise ValueError(f"unknown ignition keys at index {index}: {sorted(unknown_event)}")
        if "row" not in event or "col" not in event:
            raise ValueError(f"ignition {index} requires row and col")
        ignitions.append(
            IgnitionEvent(
                row=event["row"],
                col=event["col"],
                time_s=event.get("time_s", 0.0),
            )
        )

    raw_output = _mapping(root.get("output"), "output")
    if set(raw_output) != {"directory"}:
        raise ValueError("output must contain exactly one 'directory' key")
    output_directory = _path(raw_output["directory"], base=base, label="output.directory")

    cell_size = root.get("cell_size_m")
    if isinstance(cell_size, bool) or not isinstance(cell_size, (int, float)):
        raise ValueError("cell_size_m must be numeric")

    d0 = behavior.get("day_of_minimum_foliar_moisture")
    if d0 is not None and (isinstance(d0, bool) or not isinstance(d0, int)):
        raise ValueError("behavior.day_of_minimum_foliar_moisture must be an integer")

    return StaticFBPRunConfig(
        inputs=inputs,
        cell_size_m=float(cell_size),
        ignitions=tuple(ignitions),
        output_directory=output_directory,
        julian_day=julian_day,
        percent_conifer=_number(behavior, "percent_conifer", 50.0),
        percent_dead_fir=_number(behavior, "percent_dead_fir", 35.0),
        grass_fuel_load_kg_m2=_number(behavior, "grass_fuel_load_kg_m2", 0.35),
        grass_curing_percent=_number(behavior, "grass_curing_percent", 80.0),
        day_of_minimum_foliar_moisture=d0,
    )
