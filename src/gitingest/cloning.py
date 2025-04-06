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
# Method: 'prefix' (https://<token>@host/...), 'oauth2' (https://oauth2:<token>@host/...), 'user' (<user>:<token>@host - requires username, not implemented)
KNOWN_HOST_AUTH = {
    "github.com": {"method": "prefix"},
    "gitlab.com": {"method": "oauth2"},
    "codeberg.org": {"method": "prefix"}, # Gitea instances often use prefix
    "bitbucket.org": {"method": "prefix", "user": "x-token-auth"}, # Bitbucket uses x-token-auth:<token>
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
    auth_url = url
    should_skip_check = False
    if access_token:
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc.lower()
            host_info = KNOWN_HOST_AUTH.get(hostname)

            if host_info:
                method = host_info["method"]
                if method == "prefix":
                    user = host_info.get("user")
                    if user:
                        auth_url = url.replace("https://", f"https://{user}:{access_token}@")
                    else:
                        auth_url = url.replace("https://", f"https://{access_token}@")
                elif method == "oauth2":
                    auth_url = url.replace("https://", f"https://oauth2:{access_token}@")
                # Add other methods if needed

                should_skip_check = True # Skip check if token is provided for a known host

        except Exception as e:
            # Ignore parsing errors, proceed with original URL
            print(f"Warning: Could not parse URL '{url}' for token auth: {e}")

    # Skip existence check only if token is provided for a known host type
    if not should_skip_check:
        if not await check_repo_exists(url):
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
