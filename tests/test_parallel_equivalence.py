from pathlib import Path
from gitingest.parallel.walker import walk_parallel
from gitingest.ingestion import _ingest_single_path as ingest
import os


def test_parallel_matches_serial(tmp_path):
    # create 50 dummy python files
    for i in range(50):
        (tmp_path / f"f{i}.py").write_text(f"def f{i}(): pass\n")

    serial = [c for p in tmp_path.rglob("*.py") for c in ingest(p)]
    parallel = list(walk_parallel(tmp_path, ingest, max_workers=4))
    assert len(serial) == len(parallel)
