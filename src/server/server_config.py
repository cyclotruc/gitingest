""" Configuration for the server. """

from pathlib import Path

from fastapi.templating import Jinja2Templates

MAX_DISPLAY_SIZE: int = 300_000
DELETE_REPO_AFTER: int = 60 * 60  # In seconds

OUTPUT_FILE_PATH = "digest.txt"
TMP_BASE_PATH = Path("/tmp/gitingest")

EXAMPLE_REPOS: list[dict[str, str]] = [
    {"name": "Gitingest", "url": "https://github.com/cyclotruc/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Tldraw", "url": "https://github.com/tldraw/tldraw"},
    {"name": "ApiAnalytics", "url": "https://github.com/tom-draper/api-analytics"},
]

templates = Jinja2Templates(directory="templates")
