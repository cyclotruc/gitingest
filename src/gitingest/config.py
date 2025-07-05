"""Configuration file for the project."""

import os
import tempfile
from pathlib import Path

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

# Configuration with environment variable support
MAX_FILE_SIZE = _get_env_var("MAX_FILE_SIZE", 10 * 1024 * 1024, int)  # Maximum size of a single file to process (10 MB)
MAX_DIRECTORY_DEPTH = _get_env_var("MAX_DIRECTORY_DEPTH", 20, int)  # Maximum depth of directory traversal
MAX_FILES = _get_env_var("MAX_FILES", 10_000, int)  # Maximum number of files to process
MAX_TOTAL_SIZE_BYTES = _get_env_var("MAX_TOTAL_SIZE_BYTES", 500 * 1024 * 1024, int)  # Maximum size of output file (500 MB)
DEFAULT_TIMEOUT = _get_env_var("DEFAULT_TIMEOUT", 60, int)  # seconds

OUTPUT_FILE_NAME = _get_env_var("OUTPUT_FILE_NAME", "digest.txt")

TMP_BASE_PATH = Path(_get_env_var("TMP_BASE_PATH", tempfile.gettempdir())) / "gitingest"
