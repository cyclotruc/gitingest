import os

from api_analytics.fastapi import Analytics
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.trustedhost import TrustedHostMiddleware

from routers import download, dynamic, index
from server_utils import limiter

# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI application
app = FastAPI()
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
