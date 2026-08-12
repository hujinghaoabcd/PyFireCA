"""Common fire-behavior contracts used by wildfire CA transition rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from typing import Protocol, TypeVar

InputT = TypeVar("InputT", contravariant=True)


def _validate_nonnegative_finite(name: str, value: float | None) -> None:
    if value is None:
        return
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class FireBehaviorResult:
    """Model-independent fire-behavior quantities consumed by CA rules.

    Parameters
    ----------
    spread_rate_m_s
        Forward/local spread rate in metres per second. Must be finite and
        non-negative.
    spread_direction_deg
        Optional direction of maximum/local spread in degrees clockwise from
        geographic north, in the half-open interval ``[0, 360)``.
    fireline_intensity_w_m
        Optional fireline intensity in watts per metre.
    flame_length_m
        Optional flame length in metres.
    diagnostics
        Optional model-specific scalar diagnostics. Transition rules should
        depend on these only when they explicitly target that behavior model.

    Notes
    -----
    PyFireCA standardizes the quantities crossing the behavior-to-CA boundary,
    not the internal equations or native inputs of each behavior model.
    Rothermel- and FBP-style implementations may therefore expose different
    typed input dataclasses while returning this common result.
    """

    spread_rate_m_s: float
    spread_direction_deg: float | None = None
    fireline_intensity_w_m: float | None = None
    flame_length_m: float | None = None
    diagnostics: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_nonnegative_finite("spread_rate_m_s", self.spread_rate_m_s)
        _validate_nonnegative_finite(
            "fireline_intensity_w_m", self.fireline_intensity_w_m
        )
        _validate_nonnegative_finite("flame_length_m", self.flame_length_m)

        direction = self.spread_direction_deg
        if direction is not None and (
            not isfinite(direction) or not 0.0 <= direction < 360.0
        ):
            raise ValueError("spread_direction_deg must be finite and in [0, 360)")

        for key, value in self.diagnostics.items():
            if not isinstance(key, str) or not key:
                raise ValueError("diagnostic names must be non-empty strings")
            if not isfinite(float(value)):
                raise ValueError(f"diagnostic {key!r} must be finite")


class FireBehaviorModel(Protocol[InputT]):
    """Structural interface implemented by a fire-behavior model.

    The input type is intentionally generic. Each scientific model owns its
    native typed input contract; only the returned behavior quantities are
    standardized for consumption by cellular-automata rules.
    """

    def compute(self, inputs: InputT) -> FireBehaviorResult:
        """Compute fire behavior for one model-specific input object."""
        ...
