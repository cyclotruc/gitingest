from gitingest.cache.disk_cache import ChunkCache
from gitingest.chunking import chunk_file
from pathlib import Path
import json


def test_cache_roundtrip(tmp_path):
    f = tmp_path / "file.py"
    f.write_text("def hi(): pass")
    cache = ChunkCache()
    chunks = chunk_file(f)
    cache.set(f, [c.__dict__ for c in chunks])
    cache.flush()

    new_cache = ChunkCache()
    assert new_cache.get(f)[0]["text"].startswith("def hi")
