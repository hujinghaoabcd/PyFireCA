"""Directional surface spread provider bridging Rothermel behavior to raster edges."""

from __future__ import annotations

from dataclasses import dataclass, field

from pyfireca.behavior._surface_ellipse import (
    SurfaceFireEllipse,
    build_surface_fire_ellipse,
    spread_rate_from_ignition_point_m_s,
)
from pyfireca.behavior.base import FireBehaviorResult
from pyfireca.behavior.rothermel import RothermelInputs
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.neighborhood import Offset
from pyfireca.propagation import north_up_square_grid_offset_bearing_deg


@dataclass(slots=True)
class HomogeneousRothermelDirectionalSpreadRate:
    """Supply Behave-style radial ROS for a static homogeneous Rothermel state.

    The model is evaluated once at construction. Each raster edge then maps its
    north-up offset to a geographic bearing, measures angular separation from
    the maximum-spread direction, and evaluates the pinned Behave
    ``FromIgnitionPoint`` surface ellipse.

    This is intentionally a homogeneous reference provider. A later spatial
    provider may evaluate different fuel/weather inputs by source cell without
    changing the arrival solver contract.
    """

    model: RothermelModel
    inputs: RothermelInputs
    _behavior: FireBehaviorResult = field(init=False, repr=False)
    _ellipse: SurfaceFireEllipse = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.model, RothermelModel):
            raise TypeError("model must be RothermelModel")
        if not isinstance(self.inputs, RothermelInputs):
            raise TypeError("inputs must be RothermelInputs")

        behavior = self.model.compute(self.inputs)
        effective_wind = float(behavior.diagnostics["effective_wind_speed_m_s"])
        ellipse = build_surface_fire_ellipse(
            behavior.spread_rate_m_s,
            effective_wind,
        )
        self._behavior = behavior
        self._ellipse = ellipse

    @property
    def behavior_result(self) -> FireBehaviorResult:
        """Return the cached maximum-spread behavior result."""

        return self._behavior

    @property
    def ellipse(self) -> SurfaceFireEllipse:
        """Return the cached surface-fire ellipse."""

        return self._ellipse

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return source-to-neighbor radial ROS for a north-up raster offset."""

        del row, col
        edge_bearing = north_up_square_grid_offset_bearing_deg(offset)
        head_direction = self._behavior.spread_direction_deg

        if head_direction is None:
            if self._ellipse.eccentricity != 0.0:
                raise RuntimeError(
                    "anisotropic ellipse requires a defined maximum-spread direction"
                )
            return self._behavior.spread_rate_m_s

        angular_offset = (edge_bearing - head_direction) % 360.0
        return spread_rate_from_ignition_point_m_s(
            self._behavior.spread_rate_m_s,
            self._ellipse.eccentricity,
            angular_offset,
        )
