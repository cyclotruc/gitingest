"""Main entry point for ingesting a source and processing its contents."""

import asyncio
import inspect
import os
import shutil
from pathlib import Path
from typing import Optional, Set, Tuple, Union

from gitingest.cloning import clone_repo
from gitingest.config import TMP_BASE_PATH
from gitingest.ingestion import ingest_query
from gitingest.query_parsing import IngestionQuery, parse_query
from gitingest.streaming import stream_remote_repo


async def ingest_async(  # pylint: disable=too-many-arguments,too-many-locals
    source: str,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    include_patterns: Optional[Union[str, Set[str]]] = None,
    exclude_patterns: Optional[Union[str, Set[str]]] = None,
    branch: Optional[str] = None,
    token: Optional[str] = None,
    output: Optional[str] = None,
    parallel: bool = False,
    incremental: bool = False,
    compress: bool = False,
    stream: bool = False,
    output_format: str = "text",
) -> Tuple[str, str, str]:
    """
    Main entry point for ingesting a source and processing its contents.
    Combines functionality for local/remote sources, private repos, and performance flags.
    """
    repo_cloned = False

    if not token:
        token = os.getenv("GITHUB_TOKEN")

    try:
        query: IngestionQuery = await parse_query(
            source=source,
            max_file_size=max_file_size,
            from_web=False,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
            token=token,
        )
        query.output_format = output_format

        if query.url:
            selected_branch = branch if branch else query.branch
            query.branch = selected_branch

            if stream:
                await asyncio.to_thread(
                    stream_remote_repo,
                    query.url,
                    branch=selected_branch,
                    subpath=query.subpath,
                    dest=query.local_path,
                )
            else:
                clone_config = query.extract_clone_config()
                clone_coroutine = clone_repo(clone_config, token=token)

                if inspect.iscoroutine(clone_coroutine):
                    if asyncio.get_event_loop().is_running():
                        await clone_coroutine
                    else:
                        asyncio.run(clone_coroutine)
                else:
                    raise TypeError("clone_repo did not return a coroutine as expected.")

            repo_cloned = True

        summary, tree, content = ingest_query(query, output_format=output_format)

        if output and output != "-":
            # The CLI handles stdout ('-'), so we only handle file writing here.
            from gitingest.output_utils import write_digest  # pylint: disable=C0415

            write_digest(tree + "\n" + content, Path(output), compress)

        return summary, tree, content
    finally:
        # Clean up the temporary directory if it was created
        if repo_cloned and Path(TMP_BASE_PATH).exists():
            shutil.rmtree(TMP_BASE_PATH, ignore_errors=True)


def ingest(  # pylint: disable=too-many-arguments
    source: str,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    include_patterns: Optional[Union[str, Set[str]]] = None,
    exclude_patterns: Optional[Union[str, Set[str]]] = None,
    branch: Optional[str] = None,
    token: Optional[str] = None,
    output: Optional[str] = None,
    parallel: bool = False,
    incremental: bool = False,
    compress: bool = False,
    stream: bool = False,
    output_format: str = "text",
) -> Tuple[str, str, str]:
    """Synchronous version of ingest_async."""
    return asyncio.run(
        ingest_async(
            source=source,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch,
            token=token,
            output=output,
            parallel=parallel,
            incremental=incremental,
            compress=compress,
            stream=stream,
            output_format=output_format,
        )
    )