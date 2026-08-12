"""Wildfire cellular-automata state definitions."""

from __future__ import annotations

from enum import IntEnum

import numpy as np
from numpy.typing import NDArray


class FireState(IntEnum):
    """Canonical cell states used by the initial PyFireCA reference model."""

    UNBURNABLE = 0
    UNBURNED = 1
    BURNING = 2
    BURNED = 3


VALID_FIRE_STATES = frozenset(int(state) for state in FireState)


def validate_state_array(state: NDArray[np.integer]) -> None:
    """Validate a two-dimensional wildfire CA state array.

    Parameters
    ----------
    state
        Integer array with shape ``(H, W)`` using values from :class:`FireState`.

    Raises
    ------
    ValueError
        If the array is not two-dimensional or contains unsupported state codes.
    TypeError
        If the array dtype is not an integer dtype.
    """

    if state.ndim != 2:
        raise ValueError(f"state must have shape (H, W); got ndim={state.ndim}")
    if not np.issubdtype(state.dtype, np.integer):
        raise TypeError(f"state must use an integer dtype; got {state.dtype}")

    unique_values = np.unique(state)
    invalid = [int(value) for value in unique_values if int(value) not in VALID_FIRE_STATES]
    if invalid:
        raise ValueError(f"state contains unsupported fire-state codes: {invalid}")


def _validate_boolean_mask(mask: NDArray[np.bool_], *, name: str) -> NDArray[np.bool_]:
    values = np.asarray(mask)
    if values.ndim != 2:
        raise ValueError(f"{name} must have shape (H, W)")
    if values.dtype != np.bool_:
        raise TypeError(f"{name} must use a boolean dtype")
    return values


def build_initial_state(
    domain_mask: NDArray[np.bool_],
    ignition_mask: NDArray[np.bool_] | None = None,
) -> NDArray[np.uint8]:
    """Build the canonical initial CA state from explicit domain semantics.

    ``domain_mask`` is ``True`` where the simulation domain is valid. Cells
    outside the domain become :class:`FireState.UNBURNABLE`; valid cells begin
    as :class:`FireState.UNBURNED`. An optional boolean ``ignition_mask`` marks
    valid-domain cells that start in :class:`FireState.BURNING`.

    NoData interpretation does not occur here. Callers must decide how source
    data produce ``domain_mask`` before invoking this state-level function.
    """

    domain = _validate_boolean_mask(domain_mask, name="domain_mask")
    state = np.full(domain.shape, int(FireState.UNBURNABLE), dtype=np.uint8)
    state[domain] = int(FireState.UNBURNED)

    if ignition_mask is None:
        return state

    ignition = _validate_boolean_mask(ignition_mask, name="ignition_mask")
    if ignition.shape != domain.shape:
        raise ValueError(
            f"ignition_mask shape {ignition.shape} does not match domain_mask shape {domain.shape}"
        )
    if np.any(ignition & ~domain):
        raise ValueError("ignition_mask cannot ignite cells outside the valid simulation domain")

    state[ignition] = int(FireState.BURNING)
    return state
