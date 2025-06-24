"""Simple on-disk cache for incremental ingestion."""

import hashlib
import json
from pathlib import Path

CACHE_DIR = Path.home() / ".gitingestcache"
CACHE_FILE = CACHE_DIR / "chunks.json"


def _sha(path: Path) -> str:
    """Return a SHA1 hash for a path incorporating mtime."""

    h = hashlib.sha1()
    h.update(str(path).encode())
    h.update(str(path.stat().st_mtime_ns).encode())
    return h.hexdigest()


class ChunkCache:
    """Disk-backed mapping from file SHA to stored chunks."""

    def __init__(self) -> None:
        CACHE_DIR.mkdir(exist_ok=True)
        if CACHE_FILE.exists():
            self.data = json.loads(CACHE_FILE.read_text())
        else:
            self.data = {}

    def get(self, path: Path):
        """Return cached chunks for a path if available.

        Parameters
        ----------
        path : Path
            File path being ingested.

        Returns
        -------
        list[dict] | None
            Cached chunk data or ``None`` if absent.
        """
        return self.data.get(_sha(path))

    def set(self, path: Path, chunks: list[dict]):
        """Store chunks for a path.

        Parameters
        ----------
        path : Path
            File path being ingested.
        chunks : list[dict]
            Chunk dictionaries to store.
        """
        self.data[_sha(path)] = chunks

    def flush(self):
        """Write cache contents to disk."""
        CACHE_FILE.write_text(json.dumps(self.data))