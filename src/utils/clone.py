import asyncio
from typing import Tuple

from .decorators import async_timeout
from config import CLONE_TIMEOUT

async def check_repo_exists(url: str) -> Tuple[bool, str]:
    """
    Check if a repository exists and is accessible.
    Returns a tuple of (exists: bool, error_message: str)
    """
    proc = await asyncio.create_subprocess_exec(
        "git",
        "ls-remote",
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        return False
    return True

@async_timeout(CLONE_TIMEOUT)
async def clone_repo(query: dict) -> str:
    if not await check_repo_exists(query['url']):
        raise ValueError("Repository not found, make sure it is public")
        
    if query['commit']:
        proc = await asyncio.create_subprocess_exec(
            "git", 
            "clone",
            "--single-branch",
            query['url'],
            query['local_path'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        
        proc = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            query['local_path'],
            "checkout",
            query['branch'],
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
    elif query['branch'] != 'main' and query['branch'] != 'master' and query['branch']:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone", 
            "--depth=1",
            "--single-branch",
            "--branch",
            query['branch'],
            query['url'],
            query['local_path'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth=1",
            "--single-branch",
            query['url'],
            query['local_path'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
    await proc.communicate()
