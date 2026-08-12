"""Static spatially heterogeneous Rothermel directional edge provider."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pyfireca.behavior.rothermel import RothermelInputs
from pyfireca.behavior.rothermel_directional import HomogeneousRothermelDirectionalSpreadRate
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.neighborhood import Offset

RothermelInputsProvider = Callable[[int, int], RothermelInputs]


@dataclass(slots=True)
class StaticSpatialRothermelDirectionalSpreadRate:
    """Provide source-cell directional ROS for a heterogeneous static landscape.

    ``inputs_provider(row, col)`` supplies one complete :class:`RothermelInputs`
    snapshot for the source cell. The first time a source cell is evaluated, its
    Rothermel maximum-spread behavior and surface ellipse are computed and cached.
    All outgoing edges from that source reuse the cached behavior state.

    The edge semantic is intentionally explicit:

    **the source cell determines the outgoing edge rate of spread.**

    No source/target averaging is performed. Such averaging would be a distinct
    model assumption and should be implemented and validated as a separate
    provider rather than hidden inside this baseline.

    This class is static: if fuel or weather changes with physical time, use a
    future time-dependent scheduler/provider rather than mutating the values
    behind ``inputs_provider`` after they have been cached.
    """

    model: RothermelModel
    inputs_provider: RothermelInputsProvider
    _cell_providers: dict[tuple[int, int], HomogeneousRothermelDirectionalSpreadRate] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.model, RothermelModel):
            raise TypeError("model must be RothermelModel")
        if not callable(self.inputs_provider):
            raise TypeError("inputs_provider must be callable")

    def _provider_at(self, row: int, col: int) -> HomogeneousRothermelDirectionalSpreadRate:
        key = (row, col)
        cached = self._cell_providers.get(key)
        if cached is not None:
            return cached

        inputs = self.inputs_provider(row, col)
        if not isinstance(inputs, RothermelInputs):
            raise TypeError(
                "inputs_provider must return RothermelInputs; "
                f"got {type(inputs).__name__} at ({row}, {col})"
            )
        provider = HomogeneousRothermelDirectionalSpreadRate(self.model, inputs)
        self._cell_providers[key] = provider
        return provider

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return radial ROS for one outgoing edge from the source cell."""

        return self._provider_at(row, col).spread_rate_m_s(row, col, offset)

    def clear_cache(self) -> None:
        """Discard cached static source-cell behavior states.

        This is primarily useful for controlled experiments/tests. Clearing the
        cache does not make the class a time-dependent solver; dynamic weather
        still requires explicit scheduling semantics.
        """

        self._cell_providers.clear()

    @property
    def cached_cell_count(self) -> int:
        """Return the number of source cells whose behavior has been evaluated."""

        return len(self._cell_providers)
