"""Public assembly of the validated Rothermel surface-fire behavior stages."""

from __future__ import annotations

from dataclasses import dataclass

from pyfireca.behavior._directions import (
    geographic_direction_from_upslope_relative_deg,
    wind_push_relative_to_upslope_deg,
)
from pyfireca.behavior._rothermel_base import compute_base_spread_result
from pyfireca.behavior._rothermel_effects import (
    apply_wind_speed_limit,
    compute_effective_wind_speed_m_s,
    compute_slope_factor,
    compute_wind_factor,
    compute_wind_speed_limit_m_s,
)
from pyfireca.behavior._rothermel_vectors import combine_wind_slope_effects
from pyfireca.behavior.base import FireBehaviorResult
from pyfireca.behavior.rothermel import RothermelInputs


@dataclass(frozen=True, slots=True)
class RothermelModel:
    """Compute validated static-fuel Rothermel surface spread behavior.

    Parameters
    ----------
    use_wind_speed_limit
        Apply Behave's optional operational effective-wind limit after wind and
        slope effects have been combined. The default is ``False`` because the
        underlying Rothermel wind factor itself does not require that limit.

    Notes
    -----
    The current public model returns validated spread rate and direction only.
    Reaction intensity is exposed as a diagnostic because it is needed by the
    optional wind-limit path, but fireline intensity and flame length remain
    unset until those output equations receive their own validation stage.
    """

    use_wind_speed_limit: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.use_wind_speed_limit, bool):
            raise TypeError("use_wind_speed_limit must be a bool")

    def compute(self, inputs: RothermelInputs) -> FireBehaviorResult:
        """Compute surface spread rate and maximum-spread direction."""

        if not isinstance(inputs, RothermelInputs):
            raise TypeError("inputs must be RothermelInputs")

        base = compute_base_spread_result(inputs.fuel, inputs.moisture)
        if base.spread_rate_m_s <= 0.0:
            return FireBehaviorResult(
                spread_rate_m_s=0.0,
                spread_direction_deg=None,
                diagnostics={
                    "base_spread_rate_m_s": base.spread_rate_m_s,
                    "reaction_intensity_w_m2": base.reaction_intensity_w_m2,
                    "characteristic_sav_m_inv": base.characteristic_sav_m_inv,
                    "packing_ratio": base.packing_ratio,
                    "relative_packing_ratio": base.relative_packing_ratio,
                    "wind_factor": 0.0,
                    "slope_factor": 0.0,
                    "effective_factor": 0.0,
                    "effective_wind_speed_m_s": 0.0,
                    "wind_speed_limit_m_s": 0.0,
                    "wind_limit_enabled": float(self.use_wind_speed_limit),
                    "wind_limit_exceeded": 0.0,
                },
            )

        slope_factor = compute_slope_factor(inputs.slope_deg, base.packing_ratio)
        wind_factor = compute_wind_factor(
            inputs.midflame_wind_speed_m_s,
            base.characteristic_sav_m_inv,
            base.relative_packing_ratio,
        )
        relative_wind_direction = wind_push_relative_to_upslope_deg(
            inputs.wind_from_direction_deg,
            inputs.aspect_deg,
        )
        combined = combine_wind_slope_effects(
            base.spread_rate_m_s,
            wind_factor=wind_factor,
            slope_factor=slope_factor,
            wind_push_relative_to_upslope_deg=relative_wind_direction,
        )

        effective_wind_speed = compute_effective_wind_speed_m_s(
            combined.effective_factor,
            base.characteristic_sav_m_inv,
            base.relative_packing_ratio,
        )
        wind_speed_limit = compute_wind_speed_limit_m_s(base.reaction_intensity_w_m2)

        spread_rate = combined.spread_rate_m_s
        wind_limit_exceeded = False
        if self.use_wind_speed_limit:
            spread_rate, wind_limit_exceeded = apply_wind_speed_limit(
                base.spread_rate_m_s,
                effective_wind_speed,
                wind_speed_limit,
                base.characteristic_sav_m_inv,
                base.relative_packing_ratio,
            )

        has_directional_effect = wind_factor > 0.0 or slope_factor > 0.0
        spread_direction = None
        if has_directional_effect and spread_rate > 0.0:
            spread_direction = geographic_direction_from_upslope_relative_deg(
                combined.direction_relative_to_upslope_deg,
                inputs.aspect_deg,
            )

        return FireBehaviorResult(
            spread_rate_m_s=spread_rate,
            spread_direction_deg=spread_direction,
            diagnostics={
                "base_spread_rate_m_s": base.spread_rate_m_s,
                "reaction_intensity_w_m2": base.reaction_intensity_w_m2,
                "characteristic_sav_m_inv": base.characteristic_sav_m_inv,
                "packing_ratio": base.packing_ratio,
                "relative_packing_ratio": base.relative_packing_ratio,
                "wind_factor": wind_factor,
                "slope_factor": slope_factor,
                "effective_factor": combined.effective_factor,
                "effective_wind_speed_m_s": effective_wind_speed,
                "wind_speed_limit_m_s": wind_speed_limit,
                "wind_limit_enabled": float(self.use_wind_speed_limit),
                "wind_limit_exceeded": float(wind_limit_exceeded),
            },
        )
