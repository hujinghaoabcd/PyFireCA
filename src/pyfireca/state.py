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
