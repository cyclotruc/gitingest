""" Main entry point for ingesting a source and processing its contents. """

import asyncio
import inspect
import shutil

from config import TMP_BASE_PATH
from gitingest.query_ingestion import run_ingest_query
from gitingest.query_parser import parse_query
from gitingest.repository_clone import CloneConfig, clone_repo


def ingest(
    source: str,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    include_patterns: list[str] | str | None = None,
    exclude_patterns: list[str] | str | None = None,
    output: str | None = None,
) -> tuple[str, str, str]:
    """
    Main entry point for ingesting a source and processing its contents.

    This function analyzes a source (URL or local path), clones the corresponding repository (if applicable),
    and processes its files according to the specified query parameters. It returns a summary, a tree-like
    structure of the files, and the content of the files. The results can optionally be written to an output file.

    Parameters
    ----------
    source : str
        The source to analyze, which can be a URL (for a GitHub repository) or a local directory path.
    max_file_size : int
        Maximum allowed file size for file ingestion. Files larger than this size are ignored, by default
        10*1024*1024 (10 MB).
    include_patterns : list[str] | str | None, optional
        Pattern or list of patterns specifying which files to include. If `None`, all files are included.
    exclude_patterns : list[str] | str | None, optional
        Pattern or list of patterns specifying which files to exclude. If `None`, no files are excluded.
    output : str | None, optional
        File path where the summary and content should be written. If `None`, the results are not written to a file.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing:
        - A summary string of the analyzed repository or directory.
        - A tree-like string representation of the file structure.
        - The content of the files in the repository or directory.

    Raises
    ------
    TypeError
        If `clone_repo` does not return a coroutine, or if the `source` is of an unsupported type.
    """
    try:
        query = parse_query(
            source=source,
            max_file_size=max_file_size,
            from_web=False,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
        )
        if query["url"]:

            # Extract relevant fields for CloneConfig
            clone_config = CloneConfig(
                url=query["url"],
                local_path=str(query["local_path"]),
                commit=query.get("commit"),
                branch=query.get("branch"),
            )
            clone_result = clone_repo(clone_config)

            if inspect.iscoroutine(clone_result):
                asyncio.run(clone_result)
            else:
                raise TypeError("clone_repo did not return a coroutine as expected.")

        summary, tree, content = run_ingest_query(query)

        if output is not None:
            with open(output, "w", encoding="utf-8") as f:
                f.write(tree + "\n" + content)

        return summary, tree, content
    finally:
        # Clean up the temporary directory if it was created
        if query["url"]:
            # Clean up the temporary directory
            shutil.rmtree(TMP_BASE_PATH, ignore_errors=True)
