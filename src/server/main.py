"""Main module for the FastAPI application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from starlette.middleware.trustedhost import TrustedHostMiddleware

from server.routers import dynamic, index, ingest
from server.server_config import templates
from server.server_utils import lifespan, limiter, rate_limit_exception_handler

# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI application with lifespan
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.state.limiter = limiter

# Register the custom exception handler for rate limits
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)


# Mount static files dynamically to serve CSS, JS, and other static assets
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify that the server is running.

    **Returns**

    - **dict[str, str]**: A JSON object with a "status" key indicating the server's health status.

    """
    return {"status": "healthy"}


@app.head("/", include_in_schema=False)
async def head_root() -> HTMLResponse:
    """Respond to HTTP HEAD requests for the root URL.

    Mirrors the headers and status code of the index page.

    Returns
    -------
    HTMLResponse
        An empty HTML response with appropriate headers.

    """
    return HTMLResponse(content=None, headers={"content-type": "text/html; charset=utf-8"})


@app.get("/robots.txt", include_in_schema=False)
async def robots() -> FileResponse:
    """Serve the ``robots.txt`` file to guide search engine crawlers.

    Returns
    -------
    FileResponse
        The ``robots.txt`` file located in the static directory.

    """
    return FileResponse("static/robots.txt")


@app.get("/llm.txt")
async def llm_txt() -> FileResponse:
    """Serve the ``llm.txt`` file to provide information about the site to LLMs.

    Returns
    -------
    FileResponse
        The ``llm.txt`` file located in the static directory.

    """
    return FileResponse("static/llm.txt")


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui(request: Request) -> HTMLResponse:
    """Swagger UI documentation."""
    return templates.TemplateResponse("swagger_ui.jinja", {"request": request})


@app.get("/api", include_in_schema=True)
@app.get("/api/", include_in_schema=False)
def openapi_json_get() -> JSONResponse:
    """Return the OpenAPI schema (openapi.json)."""
    return JSONResponse(app.openapi())


@app.post("/api", include_in_schema=False)
@app.post("/api/", include_in_schema=False)
def openapi_json_post() -> JSONResponse:
    """Return the OpenAPI schema (openapi.json)."""
    return JSONResponse(app.openapi())


@app.put("/api", include_in_schema=False)
@app.put("/api/", include_in_schema=False)
def openapi_json_put() -> JSONResponse:
    """Return the OpenAPI schema (openapi.json)."""
    return JSONResponse(app.openapi())


@app.delete("/api", include_in_schema=False)
@app.delete("/api/", include_in_schema=False)
def openapi_json_delete() -> JSONResponse:
    """Return the OpenAPI schema (openapi.json)."""
    return JSONResponse(app.openapi())


@app.options("/api", include_in_schema=False)
@app.options("/api/", include_in_schema=False)
def openapi_json_options() -> JSONResponse:
    """Return the OpenAPI schema (openapi.json)."""
    return JSONResponse(app.openapi())


@app.head("/api", include_in_schema=False)
@app.head("/api/", include_in_schema=False)
def openapi_json_head() -> JSONResponse:
    """Return the OpenAPI schema (openapi.json)."""
    return JSONResponse(app.openapi())


# Include routers for modular endpoints
app.include_router(index)
app.include_router(ingest)
app.include_router(dynamic)
