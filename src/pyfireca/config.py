"""Configuration objects for the baseline static wildfire simulator."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import yaml

from pyfireca.ignition import IgnitionEvent

_CONFIG_VERSION = 1
_INPUT_KEYS = (
    "fuel_model",
    "dead_1h_moisture",
    "dead_10h_moisture",
    "dead_100h_moisture",
    "live_herbaceous_moisture",
    "live_woody_moisture",
    "midflame_wind_speed",
    "wind_from_direction",
    "slope",
    "aspect",
)


@dataclass(frozen=True, slots=True)
class StaticRasterInputPaths:
    """File paths for the ten required static Rothermel raster layers."""

    fuel_model: Path
    dead_1h_moisture: Path
    dead_10h_moisture: Path
    dead_100h_moisture: Path
    live_herbaceous_moisture: Path
    live_woody_moisture: Path
    midflame_wind_speed: Path
    wind_from_direction: Path
    slope: Path
    aspect: Path

    def __post_init__(self) -> None:
        for name in _INPUT_KEYS:
            value = getattr(self, name)
            object.__setattr__(self, name, Path(value))

    def named_paths(self) -> tuple[tuple[str, Path], ...]:
        """Return required raster names and paths in deterministic order."""

        return tuple((name, getattr(self, name)) for name in _INPUT_KEYS)


@dataclass(frozen=True, slots=True)
class StaticRunConfig:
    """Resolved configuration for one baseline static wildfire simulation."""

    inputs: StaticRasterInputPaths
    cell_size_m: float
    ignitions: tuple[IgnitionEvent, ...]
    output_directory: Path
    use_wind_speed_limit: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, StaticRasterInputPaths):
            raise TypeError("inputs must be StaticRasterInputPaths")
        if not isfinite(self.cell_size_m) or self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be finite and positive")
        if not self.ignitions or not all(
            isinstance(event, IgnitionEvent) for event in self.ignitions
        ):
            raise ValueError("ignitions must contain at least one IgnitionEvent")
        if not isinstance(self.use_wind_speed_limit, bool):
            raise TypeError("use_wind_speed_limit must be a bool")
        object.__setattr__(self, "output_directory", Path(self.output_directory))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic serializable resolved configuration."""

        return {
            "version": _CONFIG_VERSION,
            "cell_size_m": self.cell_size_m,
            "use_wind_speed_limit": self.use_wind_speed_limit,
            "inputs": {name: str(path) for name, path in self.inputs.named_paths()},
            "ignitions": [
                {"row": event.row, "col": event.col, "time_s": event.time_s}
                for event in self.ignitions
            ],
            "output": {"directory": str(self.output_directory)},
        }


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _resolve_path(value: object, *, base_directory: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty path string")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_directory / path
    return path.resolve()


def load_static_run_config(path: str | Path) -> StaticRunConfig:
    """Load and strictly validate one baseline YAML configuration file."""

    config_path = Path(path).expanduser().resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = _require_mapping(raw, "configuration")

    allowed_root = {
        "version",
        "cell_size_m",
        "use_wind_speed_limit",
        "inputs",
        "ignitions",
        "output",
    }
    unknown_root = set(root) - allowed_root
    if unknown_root:
        raise ValueError(f"unknown configuration keys: {sorted(unknown_root)}")
    if root.get("version") != _CONFIG_VERSION:
        raise ValueError(f"configuration version must be {_CONFIG_VERSION}")

    base = config_path.parent
    raw_inputs = _require_mapping(root.get("inputs"), "inputs")
    missing_inputs = set(_INPUT_KEYS) - set(raw_inputs)
    unknown_inputs = set(raw_inputs) - set(_INPUT_KEYS)
    if missing_inputs:
        raise ValueError(f"missing required input rasters: {sorted(missing_inputs)}")
    if unknown_inputs:
        raise ValueError(f"unknown input raster keys: {sorted(unknown_inputs)}")
    input_kwargs = {
        name: _resolve_path(raw_inputs[name], base_directory=base, label=f"inputs.{name}")
        for name in _INPUT_KEYS
    }
    inputs = StaticRasterInputPaths(**input_kwargs)

    raw_ignitions = root.get("ignitions")
    if not isinstance(raw_ignitions, list) or not raw_ignitions:
        raise ValueError("ignitions must be a non-empty list")
    ignitions: list[IgnitionEvent] = []
    for index, raw_event in enumerate(raw_ignitions):
        event = _require_mapping(raw_event, f"ignitions[{index}]")
        unknown_event = set(event) - {"row", "col", "time_s"}
        if unknown_event:
            raise ValueError(f"unknown ignition keys at index {index}: {sorted(unknown_event)}")
        try:
            row = event["row"]
            col = event["col"]
        except KeyError as exc:
            raise ValueError(f"ignition {index} requires row and col") from exc
        ignitions.append(
            IgnitionEvent(
                row=row,
                col=col,
                time_s=event.get("time_s", 0.0),
            )
        )

    raw_output = _require_mapping(root.get("output"), "output")
    if set(raw_output) != {"directory"}:
        raise ValueError("output must contain exactly one 'directory' key")
    output_directory = _resolve_path(
        raw_output["directory"],
        base_directory=base,
        label="output.directory",
    )

    cell_size = root.get("cell_size_m")
    if isinstance(cell_size, bool) or not isinstance(cell_size, (int, float)):
        raise ValueError("cell_size_m must be numeric")
    wind_limit = root.get("use_wind_speed_limit", False)
    if not isinstance(wind_limit, bool):
        raise ValueError("use_wind_speed_limit must be a bool")

    return StaticRunConfig(
        inputs=inputs,
        cell_size_m=float(cell_size),
        ignitions=tuple(ignitions),
        output_directory=output_directory,
        use_wind_speed_limit=wind_limit,
    )
