"""Tests for performance helpers."""

import time
from pathlib import Path

import pytest

from gitingest.cache.disk_cache import ChunkCache
from gitingest.chunking import chunk_file
from gitingest.ingestion import ingest_directory_chunks


def test_incremental_cache(tmp_path: Path):
    f = tmp_path / "hello.py"
    f.write_text("print('hi')")
    chunks1 = list(chunk_file(f))
    cache = ChunkCache()
    cache.set(f, [c.__dict__ for c in chunks1])
    cache.flush()

    chunks2 = list(ingest_directory_chunks(tmp_path, incremental=True))
    assert chunks2[0]["text"] == "print('hi')"


@pytest.mark.slow
def test_parallel_speed(tmp_path: Path):
    for i in range(100):
        (tmp_path / f"f{i}.txt").write_text("x" * 10)

    start = time.perf_counter()
    list(ingest_directory_chunks(tmp_path))
    serial_time = time.perf_counter() - start

    start = time.perf_counter()
    list(ingest_directory_chunks(tmp_path, parallel=True))
    parallel_time = time.perf_counter() - start

    assert parallel_time <= serial_time
