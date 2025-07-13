"""Configuration for the server."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

MAX_DISPLAY_SIZE: int = 300_000
DELETE_REPO_AFTER: int = 60 * 60  # In seconds (1 hour)

# Slider configuration (if updated, update the logSliderToSize function in src/static/js/utils.js)
MAX_FILE_SIZE_KB: int = 100 * 1024  # 100 MB
MAX_SLIDER_POSITION: int = 500  # Maximum slider position

EXAMPLE_REPOS: list[dict[str, str]] = [
    {"name": "Gitingest", "url": "https://github.com/coderamp-labs/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Excalidraw", "url": "https://github.com/excalidraw/excalidraw"},
    {"name": "ApiAnalytics", "url": "https://github.com/tom-draper/api-analytics"},
]


# Use absolute path to templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=templates_dir)
