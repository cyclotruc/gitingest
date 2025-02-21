""" Functions to ingest and analyze a codebase directory or single file. """

from pathlib import Path
from typing import Tuple

from gitingest.config import MAX_DIRECTORY_DEPTH, MAX_FILES, MAX_TOTAL_SIZE_BYTES
from gitingest.filesystem_schema import FileSystemNode, FileSystemNodeType, FileSystemStats
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
    stats : Dict[str, int]
        The dictionary to track statistics such as file count and size.
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
        depth=parent_node.depth + 1
    )

    parent_node.children.append(child)
    parent_node.size += file_size
    parent_node.file_count += 1


def limit_exceeded(stats: FileSystemStats, depth: int) -> bool:

    if depth > MAX_DIRECTORY_DEPTH:
        print(f"Maximum depth limit ({MAX_DIRECTORY_DEPTH}) reached")
        return True

    if stats.total_files >= MAX_FILES:
        print(f"Maximum file limit ({MAX_FILES}) reached")
        return True # TODO: end recursion

    if stats.total_size >= MAX_TOTAL_SIZE_BYTES:
        print(f"Maxumum total size limit ({MAX_TOTAL_SIZE_BYTES/1024/1024:.1f}MB) reached")
        return True # TODO: end recursion

    return False
