""" This module contains functions for cloning a Git repository to a local path. """

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from gitingest.utils import async_timeout

TIMEOUT: int = 60


@dataclass
class CloneConfig:
    """
    Configuration for cloning a Git repository.

    This class holds the necessary parameters for cloning a repository to a local path, including
    the repository's URL, the target local path, and optional parameters for a specific commit or branch.

    Attributes
    ----------
    url : str
        The URL of the Git repository to clone.
    local_path : str
        The local directory where the repository will be cloned.
    commit : str, optional
        The specific commit hash to check out after cloning (default is None).
    branch : str, optional
        The branch to clone (default is None).
    """

    url: str
    local_path: str
    commit: Optional[str] = None
    branch: Optional[str] = None


@async_timeout(TIMEOUT)
async def clone_repo(config: CloneConfig) -> Tuple[bytes, bytes]:
    url: str = config.url
    local_path: str = config.local_path
    commit: Optional[str] = config.commit
    branch: Optional[str] = config.branch

    if not url:
        raise ValueError("The 'url' parameter is required.")
    if not local_path:
        raise ValueError("The 'local_path' parameter is required.")

    # Use os from the module-level import
    auth_token = os.getenv("GIT_AUTH_TOKEN", "")

    if auth_token:
        if not await _check_repo_exists(url):
            raise ValueError("Repository not found or invalid token provided.")
    else:
        if not await _check_repo_exists(url):
            raise ValueError("Repository not found, make sure it is public or that you provided a valid token.")

    if auth_token and "github.com" in url.lower() and url.startswith("https://"):
        remainder = url[len("https://"):]
        token_url = f"https://x-access-token:{auth_token}@{remainder}"
    else:
        token_url = url

    # Create parent directory if it doesn't exist
    parent_dir = Path(local_path).parent
    try:
        os.makedirs(parent_dir, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create parent directory {parent_dir}: {e}") from e

    if commit:
        clone_cmd = ["git", "clone", "--recurse-submodules", "--single-branch", token_url, local_path]
        await _run_git_command(*clone_cmd)
        checkout_cmd = ["git", "-C", local_path, "checkout", commit]
        return await _run_git_command(*checkout_cmd)

    if branch and branch.lower() not in ("main", "master"):
        clone_cmd = [
            "git",
            "clone",
            "--recurse-submodules",
            "--depth=1",
            "--single-branch",
            "--branch",
            branch,
            token_url,
            local_path,
        ]
        return await _run_git_command(*clone_cmd)

    clone_cmd = ["git", "clone", "--recurse-submodules", "--depth=1", "--single-branch", token_url, local_path]
    return await _run_git_command(*clone_cmd)




async def _check_repo_exists(url: str) -> bool:
    """
    Check if a Git repository exists at the provided URL.
    For GitHub, we use the GitHub API which properly supports authentication for private repos.
    """
    import os

    headers = ["-H", "User-Agent: Gitingest"]
    auth_token = os.getenv("GIT_AUTH_TOKEN", "")
    if auth_token:
        headers += ["-H", f"Authorization: token {auth_token}"]

    # If the URL is from GitHub, build the API URL.
    if "github.com" in url:
        # Remove protocol and possible .git suffix.
        parts = url.split("/")
        if len(parts) >= 5:
            owner = parts[3]
            repo = parts[4].replace(".git", "")
            url_to_check = f"https://api.github.com/repos/{owner}/{repo}"
        else:
            url_to_check = url
    else:
        url_to_check = url

    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-I",
        "-L",
        *headers,
        url_to_check,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()

    if proc.returncode != 0:
        return False

    response = stdout.decode()
    status_code = _get_status_code(response)

    if status_code in (200, 301):
        return True

    if status_code in (404, 302):
        return False

    raise RuntimeError(f"Unexpected status code: {status_code}")



@async_timeout(TIMEOUT)
async def fetch_remote_branch_list(url: str) -> List[str]:
    """
    Fetch the list of branches from a remote Git repository.
    Parameters
    ----------
    url : str
        The URL of the Git repository to fetch branches from.
    Returns
    -------
    List[str]
        A list of branch names available in the remote repository.
    """
    fetch_branches_command = ["git", "ls-remote", "--heads", url]
    stdout, _ = await _run_git_command(*fetch_branches_command)
    stdout_decoded = stdout.decode()

    return [
        line.split("refs/heads/", 1)[1]
        for line in stdout_decoded.splitlines()
        if line.strip() and "refs/heads/" in line
    ]


async def _run_git_command(*args: str) -> Tuple[bytes, bytes]:
    """
    Execute a Git command asynchronously and captures its output.

    Parameters
    ----------
    *args : str
        The Git command and its arguments to execute.

    Returns
    -------
    Tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the Git command.

    Raises
    ------
    RuntimeError
        If Git is not installed or if the Git command exits with a non-zero status.
    """
    # Check if Git is installed
    try:
        version_proc = await asyncio.create_subprocess_exec(
            "git",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await version_proc.communicate()
        if version_proc.returncode != 0:
            error_message = stderr.decode().strip() if stderr else "Git command not found"
            raise RuntimeError(f"Git is not installed or not accessible: {error_message}")
    except FileNotFoundError as exc:
        raise RuntimeError("Git is not installed. Please install Git before proceeding.") from exc

    # Execute the requested Git command
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        error_message = stderr.decode().strip()
        raise RuntimeError(f"Git command failed: {' '.join(args)}\nError: {error_message}")

    return stdout, stderr


def _get_status_code(response: str) -> int:
    """
    Extract the status code from an HTTP response.

    Parameters
    ----------
    response : str
        The HTTP response string.

    Returns
    -------
    int
        The status code of the response
    """
    status_line = response.splitlines()[0].strip()
    status_code = int(status_line.split(" ", 2)[1])
    return status_code
