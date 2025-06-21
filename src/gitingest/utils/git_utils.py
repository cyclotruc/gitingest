"""Utility functions for interacting with Git repositories."""

import asyncio
import base64
import re
from typing import List, Optional, Tuple

from gitingest.utils.exceptions import InvalidGitHubTokenError

GITHUB_PAT_PATTERN = r"^(?:github_pat_|ghp_)[A-Za-z0-9_]{36,}$"


async def run_command(*args: str) -> Tuple[bytes, bytes]:
    """
    Execute a shell command asynchronously and return (stdout, stderr) bytes.

    Parameters
    ----------
    *args : str
        The command and its arguments to execute.

    Returns
    -------
    Tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the command.

    Raises
    ------
    RuntimeError
        If command exits with a non-zero status.
    """
    # Execute the requested command
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        error_message = stderr.decode().strip()
        raise RuntimeError(f"Command failed: {' '.join(args)}\nError: {error_message}")

    return stdout, stderr


async def ensure_git_installed() -> None:
    """
    Ensure Git is installed and accessible on the system.

    Raises
    ------
    RuntimeError
        If Git is not installed or not accessible.
    """
    try:
        await run_command("git", "--version")
    except RuntimeError as exc:
        raise RuntimeError("Git is not installed or not accessible. Please install Git first.") from exc


async def check_repo_exists(url: str, token: Optional[str] = None) -> bool:
    """
    Check if a Git repository exists at the provided URL.

    Parameters
    ----------
    url : str
        The URL of the Git repository to check.
    token : str, optional
        GitHub personal-access token (PAT). Needed when *source* refers to a
        **private** repository. Can also be set via the ``GITHUB_TOKEN`` env var.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.

    Raises
    ------
    RuntimeError
        If the curl command returns an unexpected status code.
    """
    if token and "github.com" in url:
        return await _check_github_repo_exists(url, token)

    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-I",
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()

    if proc.returncode != 0:
        return False  # likely unreachable or private

    response = stdout.decode()
    status_line = response.splitlines()[0].strip()
    parts = status_line.split(" ")
    if len(parts) >= 2:
        status_code_str = parts[1]
        if status_code_str in ("200", "301"):
            return True
        if status_code_str in ("302", "404"):
            return False
    raise RuntimeError(f"Unexpected status line: {status_line}")


async def _check_github_repo_exists(url: str, token: Optional[str] = None) -> bool:
    """
    Return True iff the authenticated user can see `url`.

    Parameters
    ----------
    url : str
        The URL of the GitHub repository to check.
    token : str, optional
        GitHub personal-access token (PAT). Needed when *source* refers to a
        **private** repository. Can also be set via the ``GITHUB_TOKEN`` env var.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.

    Raises
    ------
    ValueError
        If the URL is not a valid GitHub repository URL.
    RuntimeError
        If the repository is not found, if the provided URL is invalid, or if the token format is invalid.
    """
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not m:
        raise ValueError(f"Un-recognised GitHub URL: {url!r}")
    owner, repo = m.groups()

    api = f"https://api.github.com/repos/{owner}/{repo}"
    cmd = [
        "curl",
        "--silent",
        "--location",
        "--write-out",
        "%{http_code}",
        "-o",
        "/dev/null",
        "-H",
        "Accept: application/vnd.github+json",
    ]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd.append(api)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    status = stdout.decode()[-3:]  # just the %{http_code}

    if status == "200":
        return True
    if status == "404":
        return False
    if status in ("401", "403"):
        raise RuntimeError("Token invalid or lacks permissions")
    raise RuntimeError(f"GitHub API returned unexpected HTTP {status}")


async def fetch_remote_branch_list(url: str, token: Optional[str] = None) -> List[str]:
    """
    Fetch the list of branches from a remote Git repository.

    Parameters
    ----------
    url : str
        The URL of the Git repository to fetch branches from.
    token : str, optional
        GitHub personal-access token (PAT). Needed when *source* refers to a
        **private** repository. Can also be set via the ``GITHUB_TOKEN`` env var.

    Returns
    -------
    List[str]
        A list of branch names available in the remote repository.
    """
    fetch_branches_command = ["git"]

    # Add authentication if needed
    if token and "github.com" in url:
        fetch_branches_command += ["-c", create_git_auth_header(token)]

    fetch_branches_command += ["ls-remote", "--heads", url]

    await ensure_git_installed()
    stdout, _ = await run_command(*fetch_branches_command)
    stdout_decoded = stdout.decode()

    return [
        line.split("refs/heads/", 1)[1]
        for line in stdout_decoded.splitlines()
        if line.strip() and "refs/heads/" in line
    ]


def create_git_command(base_cmd: List[str], local_path: str, url: str, token: Optional[str] = None) -> List[str]:
    """Create a git command with authentication if needed.

    Parameters
    ----------
    base_cmd : List[str]
        The base git command to start with
    local_path : str
        The local path where the git command should be executed
    url : str
        The repository URL to check if it's a GitHub repository
    token : Optional[str]
        GitHub personal access token for authentication

    Returns
    -------
    List[str]
        The git command with authentication if needed
    """
    cmd = base_cmd + ["-C", local_path]
    if token and url.startswith("https://github.com"):
        validate_github_token(token)
        cmd += ["-c", create_git_auth_header(token)]
    return cmd


def create_git_auth_header(token: str) -> str:
    """Create a Basic authentication header for GitHub git operations.

    Parameters
    ----------
    token : str
        GitHub personal access token

    Returns
    -------
    str
        The git config command for setting the authentication header
    """
    basic = base64.b64encode(f"x-oauth-basic:{token}".encode()).decode()
    return f"http.https://github.com/.extraheader=Authorization: Basic {basic}"


def validate_github_token(token: str) -> None:
    """Validate the format of a GitHub Personal Access Token.

    Parameters
    ----------
    token : str
        The GitHub token to validate

    Raises
    ------
    InvalidGitHubTokenError
        If the token format is invalid
    """
    if not re.match(GITHUB_PAT_PATTERN, token):
        raise InvalidGitHubTokenError()
