"""Configuration file for the project."""

import tempfile
from pathlib import Path

from gitingest.utils.config_utils import _get_env_var

def _get_int_env_var(key: str, default: int) -> int:
    """Get environment variable as integer with fallback to default."""
    try:
        return int(_get_env_var(key, str(default)))
    except ValueError:
        print(f"Warning: Invalid value for GITINGEST_{key}. Using default: {default}")
        return default

MAX_FILE_SIZE = _get_int_env_var("MAX_FILE_SIZE", 10 * 1024 * 1024)  # Max file size to process in bytes (10 MB)
MAX_FILES = _get_int_env_var("MAX_FILES", 10_000)  # Max number of files to process
MAX_TOTAL_SIZE_BYTES = _get_int_env_var("MAX_TOTAL_SIZE_BYTES", 500 * 1024 * 1024)  # Max output file size (500 MB)
MAX_DIRECTORY_DEPTH = _get_int_env_var("MAX_DIRECTORY_DEPTH", 20)  # Max depth of directory traversal

DEFAULT_TIMEOUT = _get_int_env_var("DEFAULT_TIMEOUT", 60)  # Default timeout for git operations in seconds

OUTPUT_FILE_NAME = _get_env_var("OUTPUT_FILE_NAME", "digest.txt")
TMP_BASE_PATH = Path(_get_env_var("TMP_BASE_PATH", tempfile.gettempdir())) / "gitingest"
