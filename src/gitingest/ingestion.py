"""Functions to ingest and analyze a codebase directory or single file."""

import warnings
from pathlib import Path
from typing import Tuple
import uuid

from gitingest import config as gitingest_config
from gitingest.config import MAX_DIRECTORY_DEPTH, MAX_FILES, MAX_TOTAL_SIZE_BYTES
from gitingest.output_formatters import format_node
from gitingest.query_parsing import IngestionQuery
from gitingest.schemas import FileSystemNode, FileSystemNodeType, FileSystemStats
from gitingest.utils.ingestion_utils import _should_exclude, _should_include
from gitingest.cloud_uploader import upload_content_to_s3

try:
    import tomllib  # type: ignore[import]
except ImportError:
    import tomli as tomllib


def ingest_query(query: IngestionQuery) -> Tuple[str, str, str | None]:
    """
    Run the ingestion process for a parsed query.

    This is the main entry point for analyzing a codebase directory or single file. It processes the query
    parameters, reads the file or directory content, and generates a summary, directory structure, and file content,
    along with token estimations.

    Parameters
    ----------
    query : IngestionQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    Tuple[str, str, str | None]
        A tuple containing the summary, directory structure, and EITHER the file contents
        OR the URL to the uploaded content in cloud storage if configured and successful,
        otherwise None if upload failed.

    Raises
    ------
    ValueError
        If the path cannot be found, is not a file, or the file has no content.
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

        if not file_node.content:
            raise ValueError(f"File {file_node.name} has no content")

        summary, tree, content = format_node(file_node, query)
    else:
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

        summary, tree, content = format_node(root_node, query)

    # --- Upload to S3 if configured --- START
    content_url: str | None = None
    if gitingest_config.S3_BUCKET_NAME and gitingest_config.S3_BUCKET_NAME != "your-gitingest-bucket-name":
        object_name = f"digests/{query.slug or 'local'}/{uuid.uuid4()}.txt"
        content_url = upload_content_to_s3(
            content=content,
            bucket_name=gitingest_config.S3_BUCKET_NAME,
            object_name=object_name
        )
        if not content_url:
            warnings.warn(f"S3 upload configured but failed for {object_name}", UserWarning)
            # Decide how to handle failure: return original content or None?
            # Returning None for the third element to indicate failure/no URL
            return summary, tree, None
    else:
        # If bucket not configured, return original content
        # To enforce upload, you could raise an error here or return None
        # For now, returning original content if S3 is not set up
        # This means the return type MUST remain flexible
        # Let's change strategy: return URL if successful, original content otherwise
        pass # Keep original content

    # --- Upload to S3 if configured --- END

    # Return summary, tree, and either URL or original content
    return summary, tree, content_url if content_url else content


def apply_gitingest_file(path: Path, query: IngestionQuery) -> None:
    """
    Apply the .gitingest file to the query object.

    This function reads the .gitingest file in the specified path and updates the query object with the ignore
    patterns found in the file.

    Parameters
    ----------
    path : Path
        The path of the directory to ingest.
    query : IngestionQuery
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
    query: IngestionQuery,
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
    query : IngestionQuery
        The parsed query object containing information about the repository and query parameters.
    stats : FileSystemStats
        Statistics tracking object for the total file count and size.
    """

    if limit_exceeded(stats, node.depth):
        return

    for sub_path in node.path.iterdir():

        if query.ignore_patterns and _should_exclude(sub_path, query.local_path, query.ignore_patterns):
            continue

        if query.include_patterns and not _should_include(sub_path, query.local_path, query.include_patterns):
            continue

        if sub_path.is_symlink():
            _process_symlink(path=sub_path, parent_node=node, stats=stats, local_path=query.local_path)
        elif sub_path.is_file():
            _process_file(path=sub_path, parent_node=node, stats=stats, local_path=query.local_path)
        elif sub_path.is_dir():

            child_directory_node = FileSystemNode(
                name=sub_path.name,
                type=FileSystemNodeType.DIRECTORY,
                path_str=str(sub_path.relative_to(query.local_path)),
                path=sub_path,
                depth=node.depth + 1,
            )

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
            print(f"Warning: {sub_path} is an unknown file type, skipping")

    node.sort_children()


def _process_symlink(path: Path, parent_node: FileSystemNode, stats: FileSystemStats, local_path: Path) -> None:
    """
    Process a symlink in the file system.

    This function checks the symlink's target.

    Parameters
    ----------
    path : Path
        The full path of the symlink.
    parent_node : FileSystemNode
        The parent directory node.
    stats : FileSystemStats
        Statistics tracking object for the total file count and size.
    local_path : Path
        The base path of the repository or directory being processed.
    """
    child = FileSystemNode(
        name=path.name,
        type=FileSystemNodeType.SYMLINK,
        path_str=str(path.relative_to(local_path)),
        path=path,
        depth=parent_node.depth + 1,
    )
    stats.total_files += 1
    parent_node.children.append(child)
    parent_node.file_count += 1


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
