"""Configuration utilities."""

from __future__ import annotations

import os


def _get_env_var(key: str, default: str) -> str:
    """Get environment variable with ``GITINGEST_`` prefix.

    Parameters
    ----------
    key : str
        The name of the environment variable.
    default : str
        The default value to return if the environment variable is not set.

    Returns
    -------
    str
        The value of the environment variable as a string.

    """
    env_key = f"GITINGEST_{key}"
    value = os.environ.get(env_key)

    if value is None:
        return default

    return value
