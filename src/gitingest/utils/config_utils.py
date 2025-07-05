"""Configuration utilities."""

from __future__ import annotations

import os
from typing import Callable


def _get_env_var(key: str, default: int | str, cast_func: Callable[[str], int | str] | None = None) -> int | str:
    """Get environment variable with ``GITINGEST_`` prefix and optional type casting.

    Parameters
    ----------
    key : str
        The name of the environment variable.
    default : int | str
        The default value to return if the environment variable is not set.
    cast_func : Callable[[str], int  |  str] | None
        The function to cast the environment variable to the desired type.

    Returns
    -------
    int | str
        The value of the environment variable, cast to the desired type if provided.

    """
    env_key = f"GITINGEST_{key}"
    value = os.environ.get(env_key)

    if value is None:
        return default

    if cast_func:
        try:
            return cast_func(value)
        except (ValueError, TypeError):
            print(f"Warning: Invalid value for {env_key}: {value}. Using default: {default}")
            return default

    return value
