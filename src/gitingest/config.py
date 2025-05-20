"""Configuration file for the project."""

import tempfile
from pathlib import Path
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ingestion Configuration
MAX_FILES = int(os.environ.get("GITINGEST_MAX_FILES", 1000))
MAX_TOTAL_SIZE_MB = int(os.environ.get("GITINGEST_MAX_TOTAL_SIZE_MB", 50))
MAX_TOTAL_SIZE_BYTES = MAX_TOTAL_SIZE_MB * 1024 * 1024
MAX_FILE_SIZE_MB = int(os.environ.get("GITINGEST_MAX_FILE_SIZE_MB", 1))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_DIRECTORY_DEPTH = int(os.environ.get("GITINGEST_MAX_DIRECTORY_DEPTH", 10))

# GitHub Configuration
GITHUB_PAT = os.environ.get("GITHUB_PAT")

# Log GitHub PAT status at startup
if GITHUB_PAT:
    logger.info(f"GitHub PAT detected: {'*' * 5}{GITHUB_PAT[-4:] if len(GITHUB_PAT) > 4 else 'INVALID TOKEN'}")
    if len(GITHUB_PAT) < 10:
        logger.warning("GitHub PAT appears to be invalid (too short)")
else:
    logger.warning("No GitHub PAT found in environment variables. GitHub API rate limits will be restricted.")
    # Log all environment variables (excluding sensitive data)
    safe_env = {k: v if not k.lower().endswith(('key', 'secret', 'token', 'password', 'pat')) else '[REDACTED]' 
                for k, v in os.environ.items()}
    logger.info(f"Available environment variables: {safe_env}")

# Cloud Upload Configuration (NEW)
S3_BUCKET_NAME = os.environ.get("GITINGEST_S3_BUCKET", "your-gitingest-bucket-name") # Replace with your actual bucket or keep None

OUTPUT_FILE_NAME = "digest.txt"

# Use /tmp directory on Heroku as it's writable
TMP_BASE_PATH = Path(os.environ.get("TEMP_DIR", "/tmp/gitingest"))
os.makedirs(TMP_BASE_PATH, exist_ok=True)
