from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterable, Iterator, Any


def walk_parallel(root: Path, func: Callable[[Path], Iterable[Any]], max_workers: int = 4) -> Iterator[Any]:
    paths = list(root.rglob("*"))
    with ThreadPoolExecutor(max_workers=max_workers) as exc:
        futures = {exc.submit(func, p): p for p in paths}
        for fut in as_completed(futures):
            for item in fut.result():
                yield item
