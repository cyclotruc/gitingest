"""This module contains functions for cloning a Git repository to a local path."""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from gitingest.schemas import CloneConfig
from gitingest.utils.git_utils import check_repo_exists, ensure_git_installed, run_command
from gitingest.utils.timeout_wrapper import async_timeout

TIMEOUT: int = 60

# Known hosts and their token authentication methods (add more as needed)
# Method: 'prefix' (https://<token>@host/...),
#         'oauth2' (https://oauth2:<token>@host/...),
#         'user' (<user>:<token>@host - requires username, not implemented)
KNOWN_HOST_AUTH = {
    "github.com": {"method": "prefix"},
    "gitlab.com": {"method": "oauth2"},
    "codeberg.org": {"method": "prefix"},
    "bitbucket.org": {"method": "prefix", "user": "x-token-auth"},
}


@async_timeout(TIMEOUT)
async def clone_repo(config: CloneConfig, access_token: Optional[str] = None) -> None:
    """
    Clone a repository to a local path based on the provided configuration.

    This function handles the process of cloning a Git repository to the local file system.
    It can clone a specific branch or commit if provided, and it raises exceptions if
    any errors occur during the cloning process.

    Parameters
    ----------
    config : CloneConfig
        The configuration for cloning the repository.
    access_token : str, optional
        Access token for private repositories (optional).

    Raises
    ------
    ValueError
        If the repository is not found or if the provided URL is invalid.
    OSError
        If an error occurs while creating the parent directory for the repository.
    """
    # Extract and validate query parameters
    url: str = config.url
    local_path: str = config.local_path
    commit: Optional[str] = config.commit
    branch: Optional[str] = config.branch
    partial_clone: bool = config.subpath != "/"

    # Create parent directory if it doesn't exist
    parent_dir = Path(local_path).parent
    try:
        os.makedirs(parent_dir, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Failed to create parent directory {parent_dir}: {exc}") from exc

    # Construct authenticated URL based on host if token is provided
    auth_url = build_auth_url(url, access_token)

    # Skip existence check only if token is provided for a known host type
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    is_known_git_host = host in KNOWN_HOST_AUTH
    if not (access_token and is_known_git_host):
        exists = await check_repo_exists(url)
        if not exists:
            raise ValueError("Repository not found or inaccessible. If private, provide a token.")

    clone_cmd = ["git", "clone", "--single-branch"]
    # TODO re-enable --recurse-submodules

    if partial_clone:
        clone_cmd += ["--filter=blob:none", "--sparse"]

    if not commit:
        clone_cmd += ["--depth=1"]
        if branch and branch.lower() not in ("main", "master"):
            clone_cmd += ["--branch", branch]

    clone_cmd += [auth_url, local_path]

    # Clone the repository
    await ensure_git_installed()
    await run_command(*clone_cmd)

    if commit or partial_clone:
        checkout_cmd = ["git", "-C", local_path]

        if partial_clone:
            subpath = config.subpath.lstrip("/")
            if config.blob:
                # When ingesting from a file url (blob/branch/path/file.txt), we need to remove the file name.
                subpath = str(Path(subpath).parent.as_posix())

            checkout_cmd += ["sparse-checkout", "set", subpath]

        if commit:
            checkout_cmd += ["checkout", commit]

        # Check out the specific commit and/or subpath
        await run_command(*checkout_cmd)


def build_auth_url(url: str, access_token: Optional[str] = None) -> str:
    """
    Build an authenticated URL for cloning a repository.

    Parameters
    ----------
    url : str
        The original repository URL.
    access_token : str, optional
        Access token for private repositories (optional).

    Returns
    -------
    str
        The authenticated URL.
    """
    parsed = urlparse(url)
    final_url = url

    # Return the original URL if no access token is provided
    if access_token:
        if not parsed.scheme or not parsed.netloc:
            print(f"Warning: Could not parse URL '{url}' for token auth: invalid URL")

        host = parsed.netloc.lower()
        host_info = KNOWN_HOST_AUTH.get(host)
        if host_info:
            method = host_info["method"]
            if method == "prefix":
                user = host_info.get("user")
                if user:
                    # e.g. bitbucket.org → x-token-auth:<token>@bitbucket.org/…
                    final_url = url.replace("https://", f"https://{user}:{access_token}@", 1)
                else:
                    # e.g. github.com, codeberg.org → <token>@host/…
                    final_url = url.replace("https://", f"https://{access_token}@", 1)

            elif method == "oauth2":
                # gitlab.com → oauth2:<token>@gitlab.com/…
                final_url = url.replace("https://", f"https://oauth2:{access_token}@", 1)

            # fall‑through: shouldn't happen if KNOWN_HOST_AUTH is correct
    return final_url
