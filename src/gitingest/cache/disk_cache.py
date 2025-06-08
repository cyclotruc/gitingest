"""Simple on-disk cache for incremental ingestion."""

import hashlib
import json
from pathlib import Path

CACHE_DIR = Path.home() / ".gitingestcache"
CACHE_FILE = CACHE_DIR / "chunks.json"


def _sha(path: Path) -> str:
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
        """Return cached chunks for a path if available."""
        return self.data.get(_sha(path))

    def set(self, path: Path, chunks: list[dict]):
        """Store chunks for a path."""
        self.data[_sha(path)] = chunks

    def flush(self):
        """Write cache contents to disk."""
        CACHE_FILE.write_text(json.dumps(self.data))
