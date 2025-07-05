"""Configuration for the server."""

from __future__ import annotations

from fastapi.templating import Jinja2Templates

from gitingest.utils.config_utils import _get_env_var

MAX_DISPLAY_SIZE: int = _get_env_var("MAX_DISPLAY_SIZE", 300_000, int)
DELETE_REPO_AFTER: int = _get_env_var("DELETE_REPO_AFTER", 60 * 60, int)  # In seconds (1 hour)

# Slider configuration (if updated, update the logSliderToSize function in src/static/js/utils.js)
MAX_FILE_SIZE_KB: int = _get_env_var("MAX_FILE_SIZE_KB", 100 * 1024, int)  # 100 MB
MAX_SLIDER_POSITION: int = _get_env_var("MAX_SLIDER_POSITION", 500, int)  # Maximum slider position

EXAMPLE_REPOS: list[dict[str, str]] = [
    {"name": "Gitingest", "url": "https://github.com/cyclotruc/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Excalidraw", "url": "https://github.com/excalidraw/excalidraw"},
    {"name": "ApiAnalytics", "url": "https://github.com/tom-draper/api-analytics"},
]

templates = Jinja2Templates(directory="server/templates")
