"""This module contains functions for cloning a Git repository to a local path."""

import os
import logging
from pathlib import Path
from typing import Optional
import asyncio
import urllib.parse

from gitingest.schemas import CloneConfig
from gitingest.utils.git_utils import check_repo_exists, ensure_git_installed, run_command
from gitingest.utils.timeout_wrapper import async_timeout
from gitingest.config import GITHUB_PAT

TIMEOUT: int = 60

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@async_timeout(TIMEOUT)
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
    OSError
        If an error occurs while creating the parent directory for the repository.
    """
    # Extract and validate query parameters
    url: str = config.url
    local_path: str = config.local_path
    commit: Optional[str] = config.commit
    branch: Optional[str] = config.branch
    partial_clone: bool = config.subpath != "/"

    logger.info(f"Starting clone of repository: {url} to path: {local_path}")
    
    # Create parent directory if it doesn't exist
    parent_dir = Path(local_path).parent
    try:
        os.makedirs(parent_dir, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Failed to create parent directory {parent_dir}: {exc}") from exc

    # Check if the repository exists
    if not await check_repo_exists(url):
        raise ValueError("Repository not found, make sure it is public or you have access")

    clone_url = url
    clone_cmd = ["git", "clone", "--single-branch"]
    
    # Add GitHub PAT if available and URL is from GitHub
    env = os.environ.copy()
    if GITHUB_PAT and "github.com" in url:
        logger.info(f"Using GitHub PAT for git clone: {'*' * 5}{GITHUB_PAT[-4:] if GITHUB_PAT else 'None'}")
        
        # Instead of using environment variables, modify the URL to include the token
        # This is the recommended way to authenticate with GitHub via HTTPS after August 2021
        if url.startswith("https://github.com"):
            # Format: https://{token}@github.com/{owner}/{repo}.git
            encoded_token = urllib.parse.quote(GITHUB_PAT, safe='')
            clone_url = url.replace("https://", f"https://{encoded_token}@")
            # Add .git if not present
            if not clone_url.endswith(".git"):
                clone_url = f"{clone_url}.git"
            
            logger.info(f"Modified clone URL to use token authentication: {clone_url.replace(encoded_token, '****')}")
        else:
            # Fallback to old method
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = "git"
            env["GIT_PASSWORD"] = GITHUB_PAT
            logger.info("Added GitHub credentials to environment variables for authentication")
    else:
        logger.warning(f"No GitHub PAT found or not a GitHub URL when cloning: {url}")
        if not GITHUB_PAT:
            logger.warning("GITHUB_PAT environment variable is not set or empty in cloning.py")

    # TODO re-enable --recurse-submodules
    if partial_clone:
        clone_cmd += ["--filter=blob:none", "--sparse"]

    if not commit:
        clone_cmd += ["--depth=1"]
        if branch and branch.lower() not in ("main", "master"):
            clone_cmd += ["--branch", branch]

    clone_cmd += [clone_url, local_path]
    # Log command without exposing token
    logger.info(f"Running clone command: {' '.join([cmd.replace(GITHUB_PAT, '*****') if GITHUB_PAT and GITHUB_PAT in cmd else cmd for cmd in clone_cmd])}")

    # Clone the repository with the environment variables set
    await ensure_git_installed()
    proc = await asyncio.create_subprocess_exec(
        *clone_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        error_message = stderr.decode().strip()
        logger.error(f"Clone command failed: {error_message}")
        safe_clone_cmd = [cmd.replace(GITHUB_PAT, '*****') if GITHUB_PAT and GITHUB_PAT in cmd else cmd for cmd in clone_cmd]
        raise RuntimeError(f"Command failed: {' '.join(safe_clone_cmd)}\nError: {error_message}")
    
    logger.info("Repository cloned successfully")

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

        logger.info(f"Running checkout command: {' '.join(checkout_cmd)}")
        # Check out the specific commit and/or subpath
        await run_command(*checkout_cmd)
        logger.info("Checkout completed successfully")
