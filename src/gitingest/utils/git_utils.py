"""Utility functions for interacting with Git repositories."""

import asyncio
import logging
from typing import List, Tuple

from gitingest.config import GITHUB_PAT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


async def check_repo_exists(url: str) -> bool:
    """
    Check if a Git repository exists at the provided URL.

    Parameters
    ----------
    url : str
        The URL of the Git repository to check.
    Returns
    -------
    bool
        True if the repository exists, False otherwise.

    Raises
    ------
    RuntimeError
        If the curl command returns an unexpected status code.
    """
    curl_cmd = ["curl", "-I"]
    
    # Add GitHub PAT if available and URL is from GitHub
    if GITHUB_PAT and "github.com" in url:
        logger.info(f"GitHub PAT found: {'*' * 5}{GITHUB_PAT[-4:] if GITHUB_PAT else 'None'}")
        
        # For private repos, use the GitHub API instead of direct access
        # Extract user and repo from URL
        parts = url.replace("https://github.com/", "").split("/")
        if len(parts) >= 2:
            user = parts[0]
            repo = parts[1]
            # Use GitHub API to check repo access with PAT
            api_url = f"https://api.github.com/repos/{user}/{repo}"
            logger.info(f"Using GitHub API URL: {api_url}")
            
            curl_cmd = ["curl", "-I", "-H", f"Authorization: token {GITHUB_PAT}", api_url]
            logger.info(f"Using GitHub PAT for authentication with API URL: {api_url}")
        else:
            logger.warning(f"Could not parse GitHub URL: {url}")
            curl_cmd.extend(["-H", f"Authorization: token {GITHUB_PAT}"])
            curl_cmd.append(url)
    else:
        logger.warning(f"No GitHub PAT found or not a GitHub URL: {url}")
        if not GITHUB_PAT:
            logger.warning("GITHUB_PAT environment variable is not set or empty")
        curl_cmd.append(url)
    
    logger.info(f"Checking repo with command: {' '.join(curl_cmd).replace(GITHUB_PAT, '*****') if GITHUB_PAT else ' '.join(curl_cmd)}")
    
    proc = await asyncio.create_subprocess_exec(
        *curl_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_stderr = stderr.decode().strip()
        logger.error(f"Curl command failed with code {proc.returncode}: {error_stderr}")
        return False  # likely unreachable or private

    response = stdout.decode()
    status_line = response.splitlines()[0].strip()
    logger.info(f"GitHub API response status: {status_line}")
    parts = status_line.split(" ")
    if len(parts) >= 2:
        status_code_str = parts[1]
        if status_code_str in ("200", "301"):
            return True
        if status_code_str in ("302", "404"):
            # Added for private repos - sometimes GitHub redirects or returns 404 for non-existent or unauthorized repos
            if "github.com" in url and GITHUB_PAT:
                logger.info("Got 302/404, trying to clone directly with PAT since we have credentials")
                return True  # Let's try to clone anyway if we have PAT
            return False
    raise RuntimeError(f"Unexpected status line: {status_line}")


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
    await ensure_git_installed()
    stdout, _ = await run_command(*fetch_branches_command)
    stdout_decoded = stdout.decode()

    return [
        line.split("refs/heads/", 1)[1]
        for line in stdout_decoded.splitlines()
        if line.strip() and "refs/heads/" in line
    ]
