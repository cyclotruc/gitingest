""" Configuration file for the project. """

import tempfile
from pathlib import Path

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DIRECTORY_DEPTH = 20  # Maximum depth of directory traversal
MAX_FILES = 10_000  # Maximum number of files to process
MAX_TOTAL_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

OUTPUT_FILE_NAME = "digest.txt"

TMP_BASE_PATH = Path(tempfile.gettempdir()) / "gitingest"
