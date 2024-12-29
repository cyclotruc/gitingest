import asyncio
from dataclasses import dataclass

from gitingest.utils import AsyncTimeoutError, async_timeout

CLONE_TIMEOUT = 20

@dataclass
class CloneConfig:
    url: str
    local_path: str
    commit: str | None = None
    branch: str | None = None

async def check_repo_exists(url: str) -> bool:
   """
    Check if a repository exists at the given URL using an HTTP HEAD request.

    Parameters
    ----------
    url : str
        The URL of the repository.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.
    """
     
     proc = await asyncio.create_subprocess_exec(
            "curl",
            "-I",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return False
    # Check if stdout contains "404" status code
    stdout_str = stdout.decode()
    return "HTTP/1.1 404" not in stdout_str and "HTTP/2 404" not in stdout_str
  
async def run_git_command(*args: str) -> tuple[bytes, bytes]:
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

@async_timeout(CLONE_TIMEOUT)
async def clone_repo(query: dict) -> str:
    """
    Clones a repository to a local path based on the provided query parameters.

    Parameters
    ----------
    config : CloneConfig
        A dictionary containing the following keys:
            - url (str): The URL of the repository.
            - local_path (str): The local path to clone the repository to.
            - commit (Optional[str]): The specific commit hash to checkout.
            - branch (Optional[str]): The branch to clone. Defaults to 'main' or 'master' if not provided.

    Returns
    -------
    Tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the git commands executed.

    Raises
    ------
    ValueError
        If the repository does not exist or if required query parameters are missing.
    RuntimeError
        If any git command fails during execution.
    AsyncTimeoutError
        If the cloning process exceeds the specified timeout.
    """
    if not await check_repo_exists(query["url"]):
        raise ValueError("Repository not found, make sure it is public")

    try:
        if query["commit"]:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--single-branch",
                query["url"],
                query["local_path"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                query["local_path"],
                "checkout",
                query["branch"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        elif (
            query["branch"] != "main"
            and query["branch"] != "master"
            and query["branch"]
        ):
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--depth=1",
                "--single-branch",
                "--branch",
                query["branch"],
                query["url"],
                query["local_path"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--depth=1",
                "--single-branch",
                query["url"],
                query["local_path"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        stdout, stderr = await proc.communicate()
        return stdout, stderr
    except TimeoutError:
        stdout = "The repository cloning process timed out."
        stderr = "TimeoutError"
        return stdout, stderr
 
