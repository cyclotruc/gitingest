""" Utility functions for working with file paths. """

import os
import platform
from pathlib import Path
from typing import Union


def _normalize_path(path: Path) -> Path:
    """
    Normalize path for cross-platform compatibility.

    Parameters
    ----------
    path : Path
        The Path object to normalize.

    Returns
    -------
    Path
        The normalized path with platform-specific separators and resolved components.
    """
    return Path(os.path.normpath(str(path)))


def _is_safe_symlink(symlink_path: Path, base_path: Path) -> bool:
    """
    Check if a symlink points to a location within the base directory.

    This function resolves the target of a symlink and ensures it is within the specified
    base directory, returning `True` if it is safe, or `False` if the symlink points outside
    the base directory.

    Parameters
    ----------
    symlink_path : Path
        The path of the symlink to check.
    base_path : Path
        The base directory to ensure the symlink points within.

    Returns
    -------
    bool
        `True` if the symlink points within the base directory, `False` otherwise.
    """
    try:
        if platform.system() == "Windows":
            if not os.path.islink(str(symlink_path)):
                return False

        target_path = _normalize_path(symlink_path.resolve())
        base_resolved = _normalize_path(base_path.resolve())

        return base_resolved in target_path.parents or target_path == base_resolved
    except (OSError, ValueError):
        # If there's any error resolving the paths, consider it unsafe
        return False
