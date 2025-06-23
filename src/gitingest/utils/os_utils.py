"""Utility functions for working with the operating system."""

import os
from pathlib import Path


async def ensure_directory(path: Path) -> None:
    """
    Ensure the directory exists, creating it if necessary.

    Parameters
    ----------
    path : Path
        The path to ensure exists

    Raises
    ------
    OSError
        If the directory cannot be created
    """
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Failed to create directory {path}: {exc}") from exc
