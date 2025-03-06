""" Functions to ingest and analyze a codebase directory or single file. """

import warnings
from pathlib import Path
from typing import Tuple

from gitingest.config import MAX_DIRECTORY_DEPTH, MAX_FILES, MAX_TOTAL_SIZE_BYTES
from gitingest.filesystem_schema import FileSystemNode, FileSystemNodeType, FileSystemStats
from gitingest.output_formatters import format_directory, format_single_file
from gitingest.query_parsing import ParsedQuery
from gitingest.utils.ingestion_utils import _should_exclude, _should_include
from gitingest.utils.path_utils import _is_safe_symlink

try:
    import tomllib  # type: ignore[import]
except ImportError:
    import tomli as tomllib


def ingest_query(query: ParsedQuery) -> Tuple[str, str, str]:
    """
    Run the ingestion process for a parsed query.

    This is the main entry point for analyzing a codebase directory or single file. It processes the query
    parameters, reads the file or directory content, and generates a summary, directory structure, and file content,
    along with token estimations.

    Parameters
    ----------
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    Tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.

    Raises
    ------
    ValueError
        If the specified path cannot be found or if the file is not a text file.
    """
    subpath = Path(query.subpath.strip("/")).as_posix()
    path = query.local_path / subpath

    apply_gitingest_file(path, query)

    if not path.exists():
        raise ValueError(f"{query.slug} cannot be found")

    if (query.type and query.type == "blob") or query.local_path.is_file():
        # TODO: We do this wrong! We should still check the branch and commit!
        if not path.is_file():
            raise ValueError(f"Path {path} is not a file")

        relative_path = path.relative_to(query.local_path)

        file_node = FileSystemNode(
            name=path.name,
            type=FileSystemNodeType.FILE,
            size=path.stat().st_size,
            file_count=1,
            path_str=str(relative_path),
            path=path,
        )
        return format_single_file(file_node, query)

    root_node = FileSystemNode(
        name=path.name,
        type=FileSystemNodeType.DIRECTORY,
        path_str=str(path.relative_to(query.local_path)),
        path=path,
    )

    stats = FileSystemStats()

    _process_node(
        node=root_node,
        query=query,
        stats=stats,
    )

    return format_directory(root_node, query)


def apply_gitingest_file(path: Path, query: ParsedQuery) -> None:
    """
    Apply the .gitingest file to the query object.

    This function reads the .gitingest file in the specified path and updates the query object with the ignore
    patterns found in the file.

    Parameters
    ----------
    path : Path
        The path of the directory to ingest.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
        It should have an attribute `ignore_patterns` which is either None or a set of strings.
    """
    path_gitingest = path / ".gitingest"

    if not path_gitingest.is_file():
        return

    try:
        with path_gitingest.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        warnings.warn(f"Invalid TOML in {path_gitingest}: {exc}", UserWarning)
        return

    config_section = data.get("config", {})
    ignore_patterns = config_section.get("ignore_patterns")

    if not ignore_patterns:
        return

    # If a single string is provided, make it a list of one element
    if isinstance(ignore_patterns, str):
        ignore_patterns = [ignore_patterns]

    if not isinstance(ignore_patterns, (list, set)):
        warnings.warn(
            f"Expected a list/set for 'ignore_patterns', got {type(ignore_patterns)} in {path_gitingest}. Skipping.",
            UserWarning,
        )
        return

    # Filter out duplicated patterns
    ignore_patterns = set(ignore_patterns)

    # Filter out any non-string entries
    valid_patterns = {pattern for pattern in ignore_patterns if isinstance(pattern, str)}
    invalid_patterns = ignore_patterns - valid_patterns

    if invalid_patterns:
        warnings.warn(f"Ignore patterns {invalid_patterns} are not strings. Skipping.", UserWarning)

    if not valid_patterns:
        return

    if query.ignore_patterns is None:
        query.ignore_patterns = valid_patterns
    else:
        query.ignore_patterns.update(valid_patterns)

    return


def _process_node(
    node: FileSystemNode,
    query: ParsedQuery,
    stats: FileSystemStats,
) -> None:
    """
    Process a file or directory item within a directory.

    This function handles each file or directory item, checking if it should be included or excluded based on the
    provided patterns. It handles symlinks, directories, and files accordingly.

    Parameters
    ----------
    node : FileSystemNode
        The current directory or file node being processed.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    stats : FileSystemStats
        Statistics tracking object for the total file count and size.

    Raises
    ------
    ValueError
        If an unexpected error occurs during processing.
    """

    if limit_exceeded(stats, node.depth):
        return

    for sub_path in node.path.iterdir():

        symlink_path = None
        if sub_path.is_symlink():
            if not _is_safe_symlink(sub_path, query.local_path):
                print(f"Skipping unsafe symlink: {sub_path}")
                continue

            symlink_path = sub_path
            sub_path = sub_path.resolve()

        if sub_path in stats.visited:
            print(f"Skipping already visited path: {sub_path}")
            continue

        stats.visited.add(sub_path)

        if query.ignore_patterns and _should_exclude(sub_path, query.local_path, query.ignore_patterns):
            continue

        if query.include_patterns and not _should_include(sub_path, query.local_path, query.include_patterns):
            continue

        if sub_path.is_file():
            _process_file(path=sub_path, parent_node=node, stats=stats, local_path=query.local_path)
        elif sub_path.is_dir():

            child_directory_node = FileSystemNode(
                name=sub_path.name,
                type=FileSystemNodeType.DIRECTORY,
                path_str=str(sub_path.relative_to(query.local_path)),
                path=sub_path,
                depth=node.depth + 1,
            )

            # rename the subdir to reflect the symlink name
            if symlink_path:
                child_directory_node.name = symlink_path.name
                child_directory_node.path_str = str(symlink_path)

            _process_node(
                node=child_directory_node,
                query=query,
                stats=stats,
            )
            node.children.append(child_directory_node)
            node.size += child_directory_node.size
            node.file_count += child_directory_node.file_count
            node.dir_count += 1 + child_directory_node.dir_count

        else:
            raise ValueError(f"Unexpected error: {sub_path} is neither a file nor a directory")

    node.sort_children()


def _process_file(path: Path, parent_node: FileSystemNode, stats: FileSystemStats, local_path: Path) -> None:
    """
    Process a file in the file system.

    This function checks the file's size, increments the statistics, and reads its content.
    If the file size exceeds the maximum allowed, it raises an error.

    Parameters
    ----------
    path : Path
        The full path of the file.
    parent_node : FileSystemNode
        The dictionary to accumulate the results.
    stats : FileSystemStats
        Statistics tracking object for the total file count and size.
    local_path : Path
        The base path of the repository or directory being processed.
    """
    file_size = path.stat().st_size
    if stats.total_size + file_size > MAX_TOTAL_SIZE_BYTES:
        print(f"Skipping file {path}: would exceed total size limit")
        return

    stats.total_files += 1
    stats.total_size += file_size

    if stats.total_files > MAX_FILES:
        print(f"Maximum file limit ({MAX_FILES}) reached")
        return

    child = FileSystemNode(
        name=path.name,
        type=FileSystemNodeType.FILE,
        size=file_size,
        file_count=1,
        path_str=str(path.relative_to(local_path)),
        path=path,
        depth=parent_node.depth + 1,
    )

    parent_node.children.append(child)
    parent_node.size += file_size
    parent_node.file_count += 1


def limit_exceeded(stats: FileSystemStats, depth: int) -> bool:
    """
    Check if any of the traversal limits have been exceeded.

    This function checks if the current traversal has exceeded any of the configured limits:
    maximum directory depth, maximum number of files, or maximum total size in bytes.

    Parameters
    ----------
    stats : FileSystemStats
        Statistics tracking object for the total file count and size.
    depth : int
        The current depth of directory traversal.

    Returns
    -------
    bool
        True if any limit has been exceeded, False otherwise.
    """
    if depth > MAX_DIRECTORY_DEPTH:
        print(f"Maximum depth limit ({MAX_DIRECTORY_DEPTH}) reached")
        return True

    if stats.total_files >= MAX_FILES:
        print(f"Maximum file limit ({MAX_FILES}) reached")
        return True  # TODO: end recursion

    if stats.total_size >= MAX_TOTAL_SIZE_BYTES:
        print(f"Maxumum total size limit ({MAX_TOTAL_SIZE_BYTES/1024/1024:.1f}MB) reached")
        return True  # TODO: end recursion

    return False
