""" Main module for the FastAPI application. """

import asyncio
import os
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path

from api_analytics.fastapi import Analytics
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.trustedhost import TrustedHostMiddleware

from config import DELETE_REPO_AFTER, TMP_BASE_PATH
from routers import download, dynamic, index
from server_utils import limiter

# Load environment variables from .env file
load_dotenv()


async def remove_old_repositories():
    """
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
                if not folder.is_dir():
                    continue

                # Skip if folder is not old enough
                if current_time - folder.stat().st_ctime <= DELETE_REPO_AFTER:
                    continue

                await process_folder(folder)

        except Exception as e:
            print(f"Error in remove_old_repositories: {e}")

        await asyncio.sleep(60)


async def process_folder(folder: Path) -> None:
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.

    Parameters
    ----------
    _ : FastAPI
        The FastAPI application instance (unused).

    Yields
    -------
    None
        Yields control back to the FastAPI application while the background task runs.
    """
    task = asyncio.create_task(remove_old_repositories())

    yield
    # Cancel the background task on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# Initialize the FastAPI application with lifespan
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter


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


# Register the custom exception handler for rate limits
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

# Mount static files to serve CSS, JS, and other static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up API analytics middleware if an API key is provided
if app_analytics_key := os.getenv("API_ANALYTICS_KEY"):
    app.add_middleware(Analytics, api_key=app_analytics_key)

# Fetch allowed hosts from the environment or use the default values
allowed_hosts = os.getenv("ALLOWED_HOSTS")
if allowed_hosts:
    allowed_hosts = allowed_hosts.split(",")
else:
    # Define the default allowed hosts for the application
    default_allowed_hosts = ["gitingest.com", "*.gitingest.com", "localhost", "127.0.0.1"]
    allowed_hosts = default_allowed_hosts

# Add middleware to enforce allowed hosts
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Set up template rendering
templates = Jinja2Templates(directory="templates")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify that the server is running.

    Returns
    -------
    dict[str, str]
        A JSON object with a "status" key indicating the server's health status.
    """
    return {"status": "healthy"}


@app.head("/")
async def head_root() -> HTMLResponse:
    """
    Respond to HTTP HEAD requests for the root URL.

    Mirrors the headers and status code of the index page.

    Returns
    -------
    HTMLResponse
        An empty HTML response with appropriate headers.
    """
    return HTMLResponse(content=None, headers={"content-type": "text/html; charset=utf-8"})


@app.get("/api/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request) -> HTMLResponse:
    """
    Render the API documentation page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.

    Returns
    -------
    HTMLResponse
        A rendered HTML page displaying API documentation.
    """
    return templates.TemplateResponse("api.jinja", {"request": request})


@app.get("/robots.txt")
async def robots() -> FileResponse:
    """
    Serve the `robots.txt` file to guide search engine crawlers.

    Returns
    -------
    FileResponse
        The `robots.txt` file located in the static directory.
    """
    return FileResponse("static/robots.txt")


# Include routers for modular endpoints
app.include_router(index)
app.include_router(download)
app.include_router(dynamic)
