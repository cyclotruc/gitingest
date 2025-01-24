""" Utility functions for the FastAPI server. """

import asyncio
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import DELETE_REPO_AFTER, TMP_BASE_PATH


async def rate_limit_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Custom exception handler for rate-limiting errors.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    exc : Exception
        The exception raised, expected to be RateLimitExceeded.

    Returns
    -------
    Response
        A response indicating that the rate limit has been exceeded.

    Raises
    ------
    exc
        If the exception is not a RateLimitExceeded error, it is re-raised.
    """
    if isinstance(exc, RateLimitExceeded):
        # Delegate to the default rate limit handler
        return _rate_limit_exceeded_handler(request, exc)
    # Re-raise other exceptions
    raise exc


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifecycle manager for handling startup and shutdown events for the FastAPI application.

    Parameters
    ----------
    _ : FastAPI
        The FastAPI application instance (unused).

    Yields
    -------
    None
        Yields control back to the FastAPI application while the background task runs.
    """
    task = asyncio.create_task(_remove_old_repositories())

    yield
    # Cancel the background task on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def _remove_old_repositories():
    """
    Periodically remove old repository folders.

    Background task that runs periodically to clean up old repository directories.

    This task:
    - Scans the TMP_BASE_PATH directory every 60 seconds
    - Removes directories older than DELETE_REPO_AFTER seconds
    - Before deletion, logs repository URLs to history.txt if a matching .txt file exists
    - Handles errors gracefully if deletion fails

    The repository URL is extracted from the first .txt file in each directory,
    assuming the filename format: "owner-repository.txt"
    """
    while True:
        try:
            if not TMP_BASE_PATH.exists():
                await asyncio.sleep(60)
                continue

            current_time = time.time()

            for folder in TMP_BASE_PATH.iterdir():
                if folder.is_dir():
                    continue

                # Skip if folder is not old enough
                if current_time - folder.stat().st_ctime <= DELETE_REPO_AFTER:
                    continue

                await _process_folder(folder)

        except Exception as e:
            print(f"Error in _remove_old_repositories: {e}")

        await asyncio.sleep(60)


async def _process_folder(folder: Path) -> None:
    """
    Process a single folder for deletion and logging.

    Parameters
    ----------
    folder : Path
        The path to the folder to be processed.
    """
    # Try to log repository URL before deletion
    try:
        txt_files = [f for f in folder.iterdir() if f.suffix == ".txt"]

        # Extract owner and repository name from the filename
        if txt_files and "-" in (filename := txt_files[0].stem):
            owner, repo = filename.split("-", 1)
            repo_url = f"{owner}/{repo}"

            with open("history.txt", mode="a", encoding="utf-8") as history:
                history.write(f"{repo_url}\n")

    except Exception as e:
        print(f"Error logging repository URL for {folder}: {e}")

    # Delete the folder
    try:
        shutil.rmtree(folder)
    except Exception as e:
        print(f"Error deleting {folder}: {e}")
