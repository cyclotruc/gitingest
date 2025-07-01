"""Main entry point for ingesting a source and processing its contents."""

from __future__ import annotations

import asyncio
import inspect
import shutil
import sys
from pathlib import Path

from gitingest.clone import clone_repo
from gitingest.config import MAX_FILE_SIZE
from gitingest.ingestion import ingest_query
from gitingest.query_parser import IngestionQuery, parse_query
from gitingest.utils.auth import resolve_token
from gitingest.utils.ignore_patterns import load_ignore_patterns


async def ingest_async(
    source: str,
    *,
    max_file_size: int = MAX_FILE_SIZE,  # 10 MB
    include_patterns: str | set[str] | None = None,
    exclude_patterns: str | set[str] | None = None,
    branch: str | None = None,
    include_gitignored: bool = False,
    token: str | None = None,
    output: str | None = None,
) -> tuple[str, str, str]:
    """Ingest a source and process its contents.

    This function analyzes a source (URL or local path), clones the corresponding repository (if applicable),
    and processes its files according to the specified query parameters. It returns a summary, a tree-like
    structure of the files, and the content of the files. The results can optionally be written to an output file.

    Parameters
    ----------
    source : str
        The source to analyze, which can be a URL (for a Git repository) or a local directory path.
    max_file_size : int
        Maximum allowed file size for file ingestion. Files larger than this size are ignored (default: 10 MB).
    include_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to include. If ``None``, all files are included.
    exclude_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to exclude. If ``None``, no files are excluded.
    branch : str | None
        The branch to clone and ingest (default: the default branch).
    include_gitignored : bool
        If ``True``, include files ignored by ``.gitignore`` and ``.gitingestignore`` (default: ``False``).
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.
    output : str | None
        File path where the summary and content should be written.
        If ``"-"`` (dash), the results are written to ``stdout``.
        If ``None``, the results are not written to a file.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing:
        - A summary string of the analyzed repository or directory.
        - A tree-like string representation of the file structure.
        - The content of the files in the repository or directory.

    """
    token = resolve_token(token)

    query: IngestionQuery = await parse_query(
        source=source,
        max_file_size=max_file_size,
        from_web=False,
        include_patterns=include_patterns,
        ignore_patterns=exclude_patterns,
        token=token,
    )

    if not include_gitignored:
        _apply_gitignores(query)

    if branch:
        query.branch = branch

    repo_cloned = False
    try:
        await _clone_if_remote(query, token=token)
        repo_cloned = bool(query.url)

        summary, tree, content = ingest_query(query)
        await _write_output(tree, content=content, target=output)

        return summary, tree, content
    finally:
        # Clean up the temporary directory for the repository
        if repo_cloned:
            shutil.rmtree(query.local_path.parent)


def ingest(
    source: str,
    *,
    max_file_size: int = MAX_FILE_SIZE,
    include_patterns: str | set[str] | None = None,
    exclude_patterns: str | set[str] | None = None,
    branch: str | None = None,
    include_gitignored: bool = False,
    token: str | None = None,
    output: str | None = None,
) -> tuple[str, str, str]:
    """Provide a synchronous wrapper around ``ingest_async``.

    This function analyzes a source (URL or local path), clones the corresponding repository (if applicable),
    and processes its files according to the specified query parameters. It returns a summary, a tree-like
    structure of the files, and the content of the files. The results can optionally be written to an output file.

    Parameters
    ----------
    source : str
        The source to analyze, which can be a URL (for a Git repository) or a local directory path.
    max_file_size : int
        Maximum allowed file size for file ingestion. Files larger than this size are ignored (default: 10 MB).
    include_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to include. If ``None``, all files are included.
    exclude_patterns : str | set[str] | None
        Pattern or set of patterns specifying which files to exclude. If ``None``, no files are excluded.
    branch : str | None
        The branch to clone and ingest (default: the default branch).
    include_gitignored : bool
        If ``True``, include files ignored by ``.gitignore`` and ``.gitingestignore`` (default: ``False``).
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
        Can also be set via the ``GITHUB_TOKEN`` environment variable.
    output : str | None
        File path where the summary and content should be written.
        If ``"-"`` (dash), the results are written to ``stdout``.
        If ``None``, the results are not written to a file.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing:
        - A summary string of the analyzed repository or directory.
        - A tree-like string representation of the file structure.
        - The content of the files in the repository or directory.

    See Also
    --------
    ``ingest_async`` : The asynchronous version of this function.

    """
    return asyncio.run(
        ingest_async(
            source=source,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch,
            include_gitignored=include_gitignored,
            token=token,
            output=output,
        ),
    )


def _apply_gitignores(query: IngestionQuery) -> None:
    """Update ``query.ignore_patterns`` in-place.

    Parameters
    ----------
    query : IngestionQuery
        The query to update.

    """
    for fname in (".gitignore", ".gitingestignore"):
        query.ignore_patterns.update(load_ignore_patterns(query.local_path, filename=fname))


async def _clone_if_remote(query: IngestionQuery, token: str | None) -> None:
    """Clone the repo if *query* points to a remote URL.

    Parameters
    ----------
    query : IngestionQuery
        The query to clone.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Raises
    ------
    TypeError
        If ``clone_repo`` does not return a coroutine.

    """
    if not query.url:  # local path ingestion
        return

    # let CLI arg override, else keep the parsed branch
    clone_cfg = query.extract_clone_config()
    clone_coroutine = clone_repo(clone_cfg, token=token)
    if not inspect.iscoroutine(clone_coroutine):
        msg = "clone_repo did not return a coroutine as expected."
        raise TypeError(msg)

    if asyncio.get_event_loop().is_running():
        await clone_coroutine
    else:  # running under sync context (unit-test, etc.)
        asyncio.run(clone_coroutine)


async def _write_output(tree: str, content: str, target: str | None) -> None:
    """Write combined output to ``target`` (``"-"`` ⇒ stdout).

    Parameters
    ----------
    tree : str
        The tree-like string representation of the file structure.
    content : str
        The content of the files in the repository or directory.
    target : str | None
        The path to the output file. If ``None``, the results are not written to a file.

    """
    data = f"{tree}\n{content}"
    loop = asyncio.get_running_loop()
    if target == "-":
        await loop.run_in_executor(None, sys.stdout.write, data)
        await loop.run_in_executor(None, sys.stdout.flush)
    elif target is not None:
        await loop.run_in_executor(None, Path(target).write_text, data, "utf-8")
