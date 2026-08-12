"""Directional spread adapter for the self-contained Canadian FBP model."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, isfinite, radians, sin, sqrt

from pyfireca.behavior.fbp import FBPComputation, FBPInputs, FBPModel
from pyfireca.neighborhood import Offset
from pyfireca.propagation import north_up_square_grid_offset_bearing_deg


@dataclass(frozen=True, slots=True)
class FBPEllipse:
    """Equilibrium fire ellipse expressed as head/back/flank rates.

    The ignition point is the origin. ``head_ros_m_min`` and
    ``back_ros_m_min`` define the two axial intercept rates, while
    ``flank_ros_m_min`` defines the semi-minor-axis growth rate.
    """

    head_ros_m_min: float
    back_ros_m_min: float
    flank_ros_m_min: float
    heading_deg: float

    @classmethod
    def from_computation(cls, result: FBPComputation) -> FBPEllipse:
        """Build an ellipse from a detailed FBP computation."""

        return cls(
            head_ros_m_min=result.head_ros_m_min,
            back_ros_m_min=result.back_ros_m_min,
            flank_ros_m_min=result.flank_ros_m_min,
            heading_deg=result.spread_direction_deg,
        )

    def directional_ros_m_min(self, bearing_deg: float) -> float:
        """Return radial equilibrium ROS from ignition toward ``bearing_deg``.

        The calculation intersects a ray from the ignition point with the
        translating ellipse defined by head, back, and flank growth rates.
        It therefore preserves the FBP head and backing rates exactly instead
        of inferring backing spread from a head-only eccentricity.
        """

        if not isfinite(bearing_deg):
            raise ValueError("bearing_deg must be finite")

        head = max(0.0, self.head_ros_m_min)
        back = max(0.0, self.back_ros_m_min)
        flank = max(0.0, self.flank_ros_m_min)
        if head <= 0.0:
            return 0.0

        # Degenerate nearly one-dimensional fire: keep the two axial rates and
        # report zero off-axis rather than divide by a vanishing semi-minor axis.
        relative = ((bearing_deg - self.heading_deg + 180.0) % 360.0) - 180.0
        if flank <= 1e-15:
            if abs(relative) <= 1e-10:
                return head
            if abs(abs(relative) - 180.0) <= 1e-10:
                return back
            return 0.0

        theta = radians(relative)
        cos_t = cos(theta)
        sin_t = sin(theta)

        semi_major_rate = 0.5 * (head + back)
        center_rate = 0.5 * (head - back)
        if semi_major_rate <= 1e-15:
            return 0.0

        quad_a = (cos_t * cos_t) / (semi_major_rate * semi_major_rate)
        quad_a += (sin_t * sin_t) / (flank * flank)
        quad_b = -2.0 * center_rate * cos_t / (semi_major_rate * semi_major_rate)
        quad_c = (center_rate * center_rate) / (semi_major_rate * semi_major_rate) - 1.0
        discriminant = max(0.0, quad_b * quad_b - 4.0 * quad_a * quad_c)
        return max(0.0, (-quad_b + sqrt(discriminant)) / (2.0 * quad_a))


@dataclass(frozen=True, slots=True)
class HomogeneousFBPDirectionalSpreadRate:
    """Direction-specific ROS provider for one uniform FBP environment."""

    inputs: FBPInputs
    model: FBPModel = field(default_factory=FBPModel)
    behavior: FBPComputation = field(init=False)
    ellipse: FBPEllipse = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, FBPInputs):
            raise TypeError("inputs must be an FBPInputs instance")
        behavior = self.model.compute_full(self.inputs)
        object.__setattr__(self, "behavior", behavior)
        object.__setattr__(self, "ellipse", FBPEllipse.from_computation(behavior))

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return FBP ellipse ROS toward one north-up raster-neighbor offset."""

        del row, col
        bearing = north_up_square_grid_offset_bearing_deg(offset)
        return self.ellipse.directional_ros_m_min(bearing) / 60.0
