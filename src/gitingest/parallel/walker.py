"""Utilities for walking directories in parallel."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Iterable, Iterator, Any


def walk_parallel(root: Path, func: Callable[[Path], Iterable[Any]], max_workers: int = 4) -> Iterator[Any]:
    """Yield results from ``func`` for every file under ``root`` using threads."""
    paths = [p for p in root.rglob("*") if p.is_file()]
    if not paths:
        return
    with ThreadPoolExecutor(max_workers=max_workers) as exc:
        for result in exc.map(func, paths):
            for item in result:
                yield item
