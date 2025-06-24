"""Helper functions for parallel ingestion workers."""

from pathlib import Path
from typing import Iterable

from gitingest.chunking import chunk_file


def ingest_file(path: Path) -> Iterable[dict]:
    """Chunk a single file and return dictionaries for JSON serialization.

    Parameters
    ----------
    path : Path
        File to chunk.

    Returns
    -------
    Iterable[dict]
        Chunk dictionaries for JSON serialization.
    """
    return [c.__dict__ for c in chunk_file(path)]
