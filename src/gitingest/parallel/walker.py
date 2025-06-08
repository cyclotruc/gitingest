"""Utilities for walking directories in parallel."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterable


def walk_parallel(root: Path, fn: Callable[[Path], list], max_workers: int = 8) -> Iterable:
    """Yield results from ``fn`` for every file under ``root`` using threads."""
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for p in root.rglob("*"):
            if p.is_file():
                futures.append(pool.submit(fn, p))
        for fut in as_completed(futures):
            yield from fut.result()
