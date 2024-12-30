import asyncio
from dataclasses import dataclass

from gitingest.utils import AsyncTimeoutError, async_timeout

CLONE_TIMEOUT: int = 20


@dataclass
class CloneConfig:
    url: str
    local_path: str
    commit: str | None = None
    branch: str | None = None
    pat: str | None = None


@async_timeout(CLONE_TIMEOUT)
async def clone_repo(config: CloneConfig) -> tuple[bytes, bytes]:
    """
    Clones a repository to a local path based on the provided configuration.

    Parameters
    ----------
    config : CloneConfig
        Configuration object containing:
            - url (str): The URL of the repository.
            - local_path (str): The local path to clone the repository to.
            - commit (Optional[str]): The specific commit hash to checkout.
            - branch (Optional[str]): The branch to clone.
            - pat (Optional[str]): Personal Access Token for authentication.

    Returns
    -------
    Tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the git commands executed.

    Raises
    ------
    ValueError
        If the repository does not exist or if required parameters are missing.
    RuntimeError
        If any git command fails during execution.
    AsyncTimeoutError
        If the cloning process exceeds the specified timeout.
    """
    # Extract and validate parameters
    url: str = config.url
    local_path: str = config.local_path
    commit: str | None = config.commit
    branch: str | None = config.branch
    pat: str | None = config.pat

    if not url:
        raise ValueError("The 'url' parameter is required.")

    if not local_path:
        raise ValueError("The 'local_path' parameter is required.")

    # Check if the repository exists
    if not await _check_repo_exists(url, pat):
        raise ValueError("Repository not found, make sure it is public or provide valid PAT")

    try:
        if commit:
            # Scenario 1: Clone and checkout a specific commit
            # Clone the repository without depth to ensure full history for checkout
            clone_cmd = ["git", "clone", "--single-branch"]
            if pat:
                url = url.replace("https://", f"https://oauth2:{pat}@")
            clone_cmd.extend([url, local_path])
            await _run_git_command(*clone_cmd)

            # Checkout the specific commit
            checkout_cmd = ["git", "-C", local_path, "checkout", commit]
            return await _run_git_command(*checkout_cmd)

        if branch and branch.lower() not in ("main", "master"):
            # Scenario 2: Clone a specific branch with shallow depth
            clone_cmd = ["git", "clone", "--depth=1", "--single-branch", "--branch", branch]
            if pat:
                url = url.replace("https://", f"https://oauth2:{pat}@")
            clone_cmd.extend([url, local_path])
            return await _run_git_command(*clone_cmd)

        # Scenario 3: Clone the default branch with shallow depth
        clone_cmd = ["git", "clone", "--depth=1", "--single-branch"]
        if pat:
            url = url.replace("https://", f"https://oauth2:{pat}@")
        clone_cmd.extend([url, local_path])
        return await _run_git_command(*clone_cmd)

    except (RuntimeError, asyncio.TimeoutError, AsyncTimeoutError):
        raise  # Re-raise the exception


async def _check_repo_exists(url: str, pat: str | None = None) -> bool:
    """
    Check if a repository exists at the given URL using an HTTP HEAD request.

    Parameters
    ----------
    url : str
        The URL of the repository.
    pat : str | None
        Personal Access Token for authentication, optional.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.
    """
    # Parse URL to get components
    parts = url.split('/')
    if len(parts) < 5:  # Need at least protocol, empty, host, username, repo
        return False
        
    host = parts[2]
    username = parts[3]
    repo = parts[4]
    
    # Construct API URL based on host
    if 'github.com' in host:
        api_url = url
    else:
        # For custom Git servers, use API v1 endpoint
        api_url = f"https://{host}/api/v1/repos/{username}/{repo}"

    cmd = ["curl", "-I"]
    if pat:
        cmd.extend(["-H", f"Authorization: token {pat}"])
    cmd.append(api_url)
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        return False
    # Check if stdout contains "404" status code
    stdout_str = stdout.decode()
    return "HTTP/1.1 404" not in stdout_str and "HTTP/2 404" not in stdout_str


async def _run_git_command(*args: str) -> tuple[bytes, bytes]:
    """
    Executes a git command asynchronously and captures its output.

    Parameters
    ----------
    *args : str
        The git command and its arguments to execute.

    Returns
    -------
    Tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the git command.

    Raises
    ------
    RuntimeError
        If the git command exits with a non-zero status.
    """
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
