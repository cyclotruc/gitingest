"""Utility functions for interacting with Git repositories."""

from __future__ import annotations

import asyncio
import base64
import re
from typing import Final
from urllib.parse import urlparse

import httpx
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from gitingest.utils.compat_func import removesuffix
from gitingest.utils.exceptions import InvalidGitHubTokenError

# GitHub Personal-Access tokens (classic + fine-grained).
#   - ghp_ / gho_ / ghu_ / ghs_ / ghr_  → 36 alphanumerics
#   - github_pat_                       → 22 alphanumerics + "_" + 59 alphanumerics
_GITHUB_PAT_PATTERN: Final[str] = r"^(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59})$"


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
    return hostname.startswith("github.")


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
        msg = f"Command failed: {' '.join(args)}\nError: {stderr.decode().strip()}"
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
    """Check whether a remote Git repository is reachable.

    Parameters
    ----------
    url : str
        URL of the Git repository to check.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    bool
        ``True`` if the repository exists, ``False`` otherwise.

    Raises
    ------
    RuntimeError
        If the host returns an unrecognised status code.

    """
    headers = {}

    if token and is_github_host(url):
        host, owner, repo = _parse_github_url(url)
        # Public GitHub vs. GitHub Enterprise
        base_api = "https://api.github.com" if host == "github.com" else f"https://{host}/api/v3"
        url = f"{base_api}/repos/{owner}/{repo}"
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.head(url, headers=headers)
        except httpx.RequestError:
            return False

    status_code = response.status_code

    if status_code == HTTP_200_OK:
        return True
    if status_code in {HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND}:
        return False
    msg = f"Unexpected HTTP status {status_code} for {url}"
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
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        msg = f"URL must start with http:// or https://: {url!r}"
        raise ValueError(msg)

    if not parsed.hostname or not parsed.hostname.startswith("github."):
        msg = f"Un-recognised GitHub hostname: {parsed.hostname!r}"
        raise ValueError(msg)

    parts = removesuffix(parsed.path, ".git").strip("/").split("/")
    expected_path_length = 2
    if len(parts) != expected_path_length:
        msg = f"Path must look like /<owner>/<repo>: {parsed.path!r}"
        raise ValueError(msg)

    owner, repo = parts
    return parsed.hostname, owner, repo


async def fetch_remote_branches_or_tags(url: str, *, ref_type: str, token: str | None = None) -> list[str]:
    """Fetch the list of branches or tags from a remote Git repository.

    Parameters
    ----------
    url : str
        The URL of the Git repository to fetch branches or tags from.
    ref_type: str
        The type of reference to fetch. Can be "branches" or "tags".
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    list[str]
        A list of branch names available in the remote repository.

    Raises
    ------
    ValueError
        If the ``ref_type`` parameter is not "branches" or "tags".

    """
    if ref_type not in ("branches", "tags"):
        msg = f"Invalid fetch type: {ref_type}"
        raise ValueError(msg)

    cmd = ["git"]

    # Add authentication if needed
    if token and is_github_host(url):
        cmd += ["-c", create_git_auth_header(token, url=url)]

    cmd += ["ls-remote"]

    fetch_tags = ref_type == "tags"
    to_fetch = "tags" if fetch_tags else "heads"

    cmd += [f"--{to_fetch}"]

    # `--refs` filters out the peeled tag objects (those ending with "^{}") (for tags)
    if fetch_tags:
        cmd += ["--refs"]

    cmd += [url]

    await ensure_git_installed()
    stdout, _ = await run_command(*cmd)

    # For each line in the output:
    # - Skip empty lines and lines that don't contain "refs/{to_fetch}/"
    # - Extract the branch or tag name after "refs/{to_fetch}/"
    return [
        line.split(f"refs/{to_fetch}/", 1)[1]
        for line in stdout.decode().splitlines()
        if line.strip() and f"refs/{to_fetch}/" in line
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

    Raises
    ------
    ValueError
        If the URL is not a valid GitHub repository URL.

    """
    hostname = urlparse(url).hostname
    if not hostname:
        msg = f"Invalid GitHub URL: {url!r}"
        raise ValueError(msg)

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
    if not re.fullmatch(_GITHUB_PAT_PATTERN, token):
        raise InvalidGitHubTokenError
