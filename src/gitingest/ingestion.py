""" Functions to ingest and analyze a codebase directory or single file. """

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from gitingest.config import MAX_DIRECTORY_DEPTH, MAX_FILES, MAX_TOTAL_SIZE_BYTES
from gitingest.exceptions import AlreadyVisitedError, MaxFileSizeReachedError, MaxFilesReachedError
from gitingest.filesystem_schema import FileSystemNode, FileSystemNodeType
from gitingest.output_formatters import format_directory, format_single_file
from gitingest.query_parsing import ParsedQuery
from gitingest.utils.ingestion_utils import _should_exclude, _should_include
from gitingest.utils.path_utils import _is_safe_symlink


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

    if not path.exists():
        raise ValueError(f"{query.slug} cannot be found")

    if query.type and query.type == "blob":
        # TODO: We do this wrong! We should still check the branch and commit!
        if not path.is_file():
            raise ValueError(f"Path {path} is not a file")

        relative_path = path.relative_to(query.local_path)

        file_node = FileSystemNode(
            name=path.name,
            type=FileSystemNodeType.FILE,
            size=path.stat().st_size,
            children=[],
            file_count=1,
            dir_count=0,
            path=str(relative_path),
            real_path=relative_path,
        )
        return format_single_file(file_node, query)

    root_node = scan_directory(path=path, query=query)
    if not root_node:
        raise ValueError(f"No files found in {path}")

    return format_directory(root_node, query)


def scan_directory(
    path: Path,
    query: ParsedQuery,
    seen_paths: Optional[Set[Path]] = None,
    depth: int = 0,
    stats: Optional[Dict[str, int]] = None,
) -> Optional[FileSystemNode]:
    """
    Recursively analyze a directory and its contents with safety limits.

    This function scans a directory and its subdirectories up to a specified depth. It checks
    for any file or directory that should be included or excluded based on the provided patterns
    and limits. It also tracks the number of files and total size processed.

    Parameters
    ----------
    path : Path
        The path of the directory to scan.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    seen_paths : Set[Path] | None, optional
        A set to track already visited paths, by default None.
    depth : int
        The current depth of directory traversal, by default 0.
    stats : Dict[str, int] | None, optional
        A dictionary to track statistics such as total file count and size, by default None.

    Returns
    -------
    FileSystemNode | None
        A FileSystemNode object representing the directory structure and contents, or `None` if limits are reached.
    """
    if seen_paths is None:
        seen_paths = set()

    if stats is None:
        stats = {"total_files": 0, "total_size": 0}

    if depth > MAX_DIRECTORY_DEPTH:
        print(f"Skipping deep directory: {path} (max depth {MAX_DIRECTORY_DEPTH} reached)")
        return None

    if stats["total_files"] >= MAX_FILES:
        print(f"Skipping further processing: maximum file limit ({MAX_FILES}) reached")
        return None

    if stats["total_size"] >= MAX_TOTAL_SIZE_BYTES:
        print(f"Skipping further processing: maximum total size ({MAX_TOTAL_SIZE_BYTES/1024/1024:.1f}MB) reached")
        return None

    real_path = path.resolve()
    if real_path in seen_paths:
        print(f"Skipping already visited path: {path}")
        return None

    seen_paths.add(real_path)

    directory_node = FileSystemNode(
        name=path.name,
        type=FileSystemNodeType.DIRECTORY,
        size=0,
        children=[],
        file_count=0,
        dir_count=0,
        path=str(path),
        real_path=path,
    )

    try:
        for sub_path in path.iterdir():
            _process_node(
                path=sub_path,
                query=query,
                node=directory_node,
                seen_paths=seen_paths,
                stats=stats,
                depth=depth,
            )
    except MaxFilesReachedError:
        print(f"Maximum file limit ({MAX_FILES}) reached.")
    except PermissionError:
        print(f"Permission denied: {path}.")

    directory_node.sort_children()
    return directory_node


def _process_node(
    path: Path,
    query: ParsedQuery,
    node: FileSystemNode,
    seen_paths: Set[Path],
    stats: Dict[str, int],
    depth: int,
) -> None:
    """
    Process a file or directory item within a directory.

    This function handles each file or directory item, checking if it should be included or excluded based on the
    provided patterns. It handles symlinks, directories, and files accordingly.

    Parameters
    ----------
    path : Path
        The full path of the file or directory to process.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    node : FileSystemNode
        The current directory or file node being processed.
    seen_paths : Set[Path]
        A set of paths that have already been visited.
    stats : Dict[str, int]
        A dictionary of statistics like the total file count and size.
    depth : int
        The current depth of directory traversal.
    """

    if query.ignore_patterns and _should_exclude(path, query.local_path, query.ignore_patterns):
        return

    if query.include_patterns and not _should_include(path, query.local_path, query.include_patterns):
        return

    symlink_path = None
    try:
        # Test if this is a symlink
        if path.is_symlink():
            if not _is_safe_symlink(path, query.local_path):
                raise RuntimeError("Unsafe ingestion from outside the repository")

            symlink_path = path
            path = path.resolve()
            if path in seen_paths:
                raise AlreadyVisitedError(str(path))

        if path.is_file():
            _process_file(path=path, file_node=node, stats=stats)

        elif path.is_dir():
            child = scan_directory(
                path=path,
                query=query,
                seen_paths=seen_paths,
                depth=depth + 1,
                stats=stats,
            )
            if child is None:
                return

            node.children.append(child)
            node.size += child.size
            node.file_count += child.file_count
            node.dir_count += 1 + child.dir_count

            # rename the subdir to reflect the symlink name
            if symlink_path:
                child.name = symlink_path.name
                child.path = str(symlink_path)

    except (MaxFileSizeReachedError, AlreadyVisitedError) as exc:
        print(exc)


def _process_file(path: Path, file_node: FileSystemNode, stats: Dict[str, int]) -> None:
    """
    Process a file in the file system.

    This function checks the file's size, increments the statistics, and reads its content.
    If the file size exceeds the maximum allowed, it raises an error.

    Parameters
    ----------
    path : Path
        The full path of the file.
    file_node : FileSystemNode
        The dictionary to accumulate the results.
    stats : Dict[str, int]
        The dictionary to track statistics such as file count and size.

    Raises
    ------
    MaxFileSizeReachedError
        If the file size exceeds the maximum limit.
    MaxFilesReachedError
        If the number of files exceeds the maximum limit.
    """
    file_size = path.stat().st_size
    if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
        print(f"Skipping file {path}: would exceed total size limit")
        raise MaxFileSizeReachedError(MAX_TOTAL_SIZE_BYTES)

    stats["total_files"] += 1
    stats["total_size"] += file_size

    if stats["total_files"] > MAX_FILES:
        print(f"Maximum file limit ({MAX_FILES}) reached")
        raise MaxFilesReachedError(MAX_FILES)

    child = FileSystemNode(
        name=path.name,
        type=FileSystemNodeType.FILE,
        size=file_size,
        children=[],
        file_count=1,
        dir_count=0,
        path=str(path),
        real_path=path,
    )

    file_node.children.append(child)
    file_node.size += file_size
    file_node.file_count += 1
