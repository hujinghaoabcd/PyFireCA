from dataclasses import dataclass

import pytest

from pyfireca.behavior import FireBehaviorResult


def test_fire_behavior_result_accepts_valid_common_quantities() -> None:
    result = FireBehaviorResult(
        spread_rate_m_s=0.5,
        spread_direction_deg=90.0,
        fireline_intensity_w_m=1250.0,
        flame_length_m=1.2,
        diagnostics={"reaction_intensity": 12.0},
    )

    assert result.spread_rate_m_s == 0.5
    assert result.spread_direction_deg == 90.0
    assert result.fireline_intensity_w_m == 1250.0


@pytest.mark.parametrize("value", [-0.1, float("nan"), float("inf")])
def test_fire_behavior_result_rejects_invalid_spread_rate(value: float) -> None:
    with pytest.raises(ValueError):
        FireBehaviorResult(spread_rate_m_s=value)


@pytest.mark.parametrize("direction", [-1.0, 360.0, float("nan")])
def test_fire_behavior_result_rejects_invalid_direction(direction: float) -> None:
    with pytest.raises(ValueError):
        FireBehaviorResult(spread_rate_m_s=0.1, spread_direction_deg=direction)


def test_fire_behavior_result_rejects_invalid_optional_quantities() -> None:
    with pytest.raises(ValueError):
        FireBehaviorResult(spread_rate_m_s=0.1, fireline_intensity_w_m=-1.0)

    with pytest.raises(ValueError):
        FireBehaviorResult(spread_rate_m_s=0.1, flame_length_m=float("inf"))


def test_fire_behavior_result_rejects_nonfinite_diagnostic() -> None:
    with pytest.raises(ValueError):
        FireBehaviorResult(
            spread_rate_m_s=0.1,
            diagnostics={"bad": float("nan")},
        )


@dataclass(frozen=True)
class _DummyInputs:
    spread_rate_m_s: float


class _DummyBehavior:
    def compute(self, inputs: _DummyInputs) -> FireBehaviorResult:
        return FireBehaviorResult(spread_rate_m_s=inputs.spread_rate_m_s)


def test_behavior_implementations_can_use_model_specific_inputs() -> None:
    model = _DummyBehavior()
    result = model.compute(_DummyInputs(spread_rate_m_s=0.25))

    assert result == FireBehaviorResult(spread_rate_m_s=0.25)
