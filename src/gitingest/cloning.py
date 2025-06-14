"""This module contains functions for cloning a Git repository to a local path."""

import os
from pathlib import Path
from typing import Optional

from gitingest.config import DEFAULT_TIMEOUT
from gitingest.schemas import CloneConfig
from gitingest.utils.git_utils import check_repo_exists, ensure_git_installed, run_command
from gitingest.utils.timeout_wrapper import async_timeout


@async_timeout(DEFAULT_TIMEOUT)
async def clone_repo(config: CloneConfig) -> None:
    """
    Clone a repository to a local path based on the provided configuration.

    This function handles the process of cloning a Git repository to the local file system.
    It can clone a specific branch or commit if provided, and it raises exceptions if
    any errors occur during the cloning process.

    Parameters
    ----------
    config : CloneConfig
        The configuration for cloning the repository.

    Raises
    ------
    ValueError
        If the repository is not found or if the provided URL is invalid.
    """
    # Extract and validate query parameters
    url: str = config.url
    local_path: str = config.local_path
    commit: Optional[str] = config.commit
    branch: Optional[str] = config.branch
    partial_clone: bool = config.subpath != "/"

    # Create parent directory if it doesn't exist
    await _ensure_directory(Path(local_path).parent)

    # Check if the repository exists
    if not await check_repo_exists(url):
        raise ValueError("Repository not found, make sure it is public")

    clone_cmd = ["git", "clone", "--single-branch"]
    # TODO: Re-enable --recurse-submodules when submodule support is needed

    if partial_clone:
        clone_cmd += ["--filter=blob:none", "--sparse"]

    if not commit:
        clone_cmd += ["--depth=1"]
        if branch and branch.lower() not in ("main", "master"):
            clone_cmd += ["--branch", branch]

    clone_cmd += [url, local_path]

    # Clone the repository
    await ensure_git_installed()
    await run_command(*clone_cmd)

    # Checkout the subpath if it is a partial clone
    if partial_clone:
        subpath = config.subpath.lstrip("/")
        if config.blob:
            # When ingesting from a file url (blob/branch/path/file.txt), we need to remove the file name.
            subpath = str(Path(subpath).parent.as_posix())

        await run_command("git", "-C", local_path, "sparse-checkout", "set", subpath)

    # Checkout the commit if it is provided
    if commit:
        await run_command("git", "-C", local_path, "checkout", commit)


async def _ensure_directory(path: Path) -> None:
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
