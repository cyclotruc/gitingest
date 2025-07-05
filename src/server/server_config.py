"""Configuration for the server."""

from __future__ import annotations

import os
from fastapi.templating import Jinja2Templates

# Helper function to get environment variables with type conversion
def _get_env_var(key: str, default, cast_func=None):
    """Get environment variable with GITINGEST_ prefix and optional type casting."""
    env_key = f"GITINGEST_{key}"
    value = os.environ.get(env_key)
    
    if value is None:
        return default
    
    if cast_func:
        try:
            return cast_func(value)
        except (ValueError, TypeError):
            print(f"Warning: Invalid value for {env_key}: {value}. Using default: {default}")
            return default
    
    return value

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
