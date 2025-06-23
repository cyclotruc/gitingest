"""This module contains functions for cloning a Git repository to a local path."""

from pathlib import Path
from typing import Optional

from gitingest.config import DEFAULT_TIMEOUT
from gitingest.schemas import CloneConfig
from gitingest.utils.git_utils import (
    check_repo_exists,
    create_git_auth_header,
    create_git_command,
    ensure_git_installed,
    run_command,
    validate_github_token,
)
from gitingest.utils.os_utils import ensure_directory
from gitingest.utils.timeout_wrapper import async_timeout


@async_timeout(DEFAULT_TIMEOUT)
async def clone_repo(config: CloneConfig, token: Optional[str] = None) -> None:
    """
    Clone a repository to a local path based on the provided configuration.

    This function handles the process of cloning a Git repository to the local file system.
    It can clone a specific branch or commit if provided, and it raises exceptions if
    any errors occur during the cloning process.

    Parameters
    ----------
    config : CloneConfig
        The configuration for cloning the repository.
    token : str, optional
        GitHub personal-access token (PAT). Needed when *source* refers to a
        **private** repository. Can also be set via the ``GITHUB_TOKEN`` env var.
        Must start with 'github_pat_' or 'gph_' for GitHub repositories.

    Raises
    ------
    ValueError
        If the repository is not found, if the provided URL is invalid, or if the token format is invalid.
    """
    # Extract and validate query parameters
    url: str = config.url
    local_path: str = config.local_path
    commit: Optional[str] = config.commit
    branch: Optional[str] = config.branch
    partial_clone: bool = config.subpath != "/"

    # Validate token if provided
    if token and url.startswith("https://github.com"):
        validate_github_token(token)

    # Create parent directory if it doesn't exist
    await ensure_directory(Path(local_path).parent)

    # Check if the repository exists
    if not await check_repo_exists(url, token=token):
        raise ValueError("Repository not found. Make sure it is public or that you have provided a valid token.")

    clone_cmd = ["git"]
    if token and url.startswith("https://github.com"):
        clone_cmd += ["-c", create_git_auth_header(token)]

    clone_cmd += ["clone", "--single-branch"]
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

        checkout_cmd = create_git_command(["git"], local_path, url, token)
        await run_command(*checkout_cmd, "sparse-checkout", "set", subpath)

    # Checkout the commit if it is provided
    if commit:
        checkout_cmd = create_git_command(["git"], local_path, url, token)
        await run_command(*checkout_cmd, "checkout", commit)
