"""Utility functions for interacting with Git repositories."""

from __future__ import annotations

import asyncio
import base64
import re
from urllib.parse import urlparse

from gitingest.utils.exceptions import InvalidGitHubTokenError

GITHUB_PAT_PATTERN = r"^(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59})$"


def is_github_host(url: str) -> bool:
    """Check if a URL is from a GitHub host (github.com or GitHub Enterprise).

    Parameters
    ----------
    url : str
        The URL to check

    Returns
    -------
    bool
        True if the URL is from a GitHub host, False otherwise

    """
    hostname = urlparse(url).hostname or ""
    return hostname == "github.com" or hostname.startswith("github.")


async def run_command(*args: str) -> tuple[bytes, bytes]:
    """Execute a shell command asynchronously and return (stdout, stderr) bytes.

    Parameters
    ----------
    *args : str
        The command and its arguments to execute.

    Returns
    -------
    tuple[bytes, bytes]
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
        msg = f"Command failed: {' '.join(args)}\nError: {error_message}"
        raise RuntimeError(msg)

    return stdout, stderr


async def ensure_git_installed() -> None:
    """Ensure Git is installed and accessible on the system.

    Raises
    ------
    RuntimeError
        If Git is not installed or not accessible.

    """
    try:
        await run_command("git", "--version")
    except RuntimeError as exc:
        msg = "Git is not installed or not accessible. Please install Git first."
        raise RuntimeError(msg) from exc


async def check_repo_exists(url: str, token: str | None = None) -> bool:
    """Check if a Git repository exists at the provided URL.

    Parameters
    ----------
    url : str
        The URL of the Git repository to check.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.

    Raises
    ------
    RuntimeError
        If the curl command returns an unexpected status code.

    """
    if token and is_github_host(url):
        return await _check_github_repo_exists(url, token=token)

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

    expected_path_length = 2
    if len(parts) >= expected_path_length:
        status = parts[1]
        if status in ("200", "301"):
            return True
        if status in ("302", "404"):
            return False
    msg = f"Unexpected status line: {status_line}"
    raise RuntimeError(msg)


async def _check_github_repo_exists(url: str, token: str | None = None) -> bool:
    """Return True iff the authenticated user can see ``url``.

    Parameters
    ----------
    url : str
        The URL of the GitHub repository to check.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.

    Raises
    ------
    RuntimeError
        If the repository is not found, if the provided URL is invalid, or if the token format is invalid.

    """
    host, owner, repo = _parse_github_url(url)

    if host == "github.com":
        api = f"https://api.github.com/repos/{owner}/{repo}"
    else:  # GitHub Enterprise
        api = f"https://{host}/api/v3/repos/{owner}/{repo}"

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
        msg = "Token invalid or lacks permissions"
        raise RuntimeError(msg)
    msg = f"GitHub API returned unexpected HTTP {status}"
    raise RuntimeError(msg)


def _parse_github_url(url: str) -> tuple[str, str, str]:
    """Parse a GitHub URL and return (hostname, owner, repo).

    Parameters
    ----------
    url : str
        The URL of the GitHub repository to parse.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing the hostname, owner, and repository name.

    Raises
    ------
    ValueError
        If the URL is not a valid GitHub repository URL.

    """
    expected_path_length = 2
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        msg = f"URL must start with http:// or https://: {url!r}"
        raise ValueError(msg)

    if not parsed.hostname or not parsed.hostname.startswith("github."):
        msg = f"Un-recognised GitHub hostname: {parsed.hostname!r}"
        raise ValueError(msg)

    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) != expected_path_length:
        msg = f"Path must look like /<owner>/<repo>: {parsed.path!r}"
        raise ValueError(msg)

    owner, repo = parts
    return parsed.hostname, owner, repo


async def fetch_remote_branch_list(url: str, token: str | None = None) -> list[str]:
    """Fetch the list of branches from a remote Git repository.

    Parameters
    ----------
    url : str
        The URL of the Git repository to fetch branches from.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.

    Returns
    -------
    list[str]
        A list of branch names available in the remote repository.

    """
    fetch_branches_command = ["git"]

    # Add authentication if needed
    if token and is_github_host(url):
        fetch_branches_command += ["-c", create_git_auth_header(token, url=url)]

    fetch_branches_command += ["ls-remote", "--heads", url]

    await ensure_git_installed()
    stdout, _ = await run_command(*fetch_branches_command)
    stdout_decoded = stdout.decode()

    return [
        line.split("refs/heads/", 1)[1]
        for line in stdout_decoded.splitlines()
        if line.strip() and "refs/heads/" in line
    ]


def create_git_command(base_cmd: list[str], local_path: str, url: str, token: str | None = None) -> list[str]:
    """Create a git command with authentication if needed.

    Parameters
    ----------
    base_cmd : list[str]
        The base git command to start with.
    local_path : str
        The local path where the git command should be executed.
    url : str
        The repository URL to check if it's a GitHub repository.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    list[str]
        The git command with authentication if needed.

    """
    cmd = [*base_cmd, "-C", local_path]
    if token and is_github_host(url):
        validate_github_token(token)
        cmd += ["-c", create_git_auth_header(token, url=url)]
    return cmd


def create_git_auth_header(token: str, url: str = "https://github.com") -> str:
    """Create a Basic authentication header for GitHub git operations.

    Parameters
    ----------
    token : str
        GitHub personal access token (PAT) for accessing private repositories.
    url : str
        The GitHub URL to create the authentication header for.
        Defaults to "https://github.com" if not provided.

    Returns
    -------
    str
        The git config command for setting the authentication header.

    """
    hostname = urlparse(url).hostname
    basic = base64.b64encode(f"x-oauth-basic:{token}".encode()).decode()
    return f"http.https://{hostname}/.extraheader=Authorization: Basic {basic}"


def validate_github_token(token: str) -> None:
    """Validate the format of a GitHub Personal Access Token.

    Parameters
    ----------
    token : str
        GitHub personal access token (PAT) for accessing private repositories.

    Raises
    ------
    InvalidGitHubTokenError
        If the token format is invalid.

    """
    if not re.match(GITHUB_PAT_PATTERN, token):
        raise InvalidGitHubTokenError
