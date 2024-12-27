import asyncio
import inspect
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Union

from gitingest.clone import clone_repo
from gitingest.ingest_from_query import ingest_from_query
from gitingest.parse_query import parse_query


def ingest(
    source: str,
    max_file_size: int = 10 * 1024 * 1024,
    include_patterns: Union[List[str], str, None] = None,
    exclude_patterns: Union[List[str], str, None] = None,
    output: Optional[str] = None,
) -> Tuple[str, str, str]:
    try:
        query = parse_query(
            source=source,
            max_file_size=max_file_size,
            from_web=False,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
        )
        if query['url']:
            clone_result = clone_repo(query)
            if inspect.iscoroutine(clone_result):
                asyncio.run(clone_result)
            else:
                raise TypeError("clone_repo did not return a coroutine as expected.")

        summary, tree, content = ingest_from_query(query)

        if output:
            with open(f"{output}", "w") as f:
                f.write(tree + "\n" + content)

        return summary, tree, content

    finally:
        # Clean up the temporary directory if it was created
        if query['url']:
            # Get parent directory two levels up from local_path (../tmp)
            cleanup_path = str(Path(query['local_path']).parents[1])
            shutil.rmtree(cleanup_path, ignore_errors=True)
