"""Functions to ingest and analyze a codebase directory or single file."""

import os
import time
import warnings
from pathlib import Path
from typing import Tuple

from gitingest.cache.disk_cache import ChunkCache
from gitingest.chunking import chunk_file
from gitingest.config import MAX_DIRECTORY_DEPTH, MAX_FILES, MAX_TOTAL_SIZE_BYTES
from gitingest.output_formatters import format_node, _gather_file_contents_jsonl
from gitingest.parallel.walker import walk_parallel
from gitingest.query_parsing import IngestionQuery
from gitingest.schemas import (
    FileSystemNode,
    FileSystemNodeType,
    FileSystemStats,
    GitingestConfig,
)
from gitingest.security.secret_scan import redact_secrets
from gitingest.utils.ingestion_utils import _should_exclude, _should_include

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older Pythons
    import tomli as tomllib  # type: ignore


def ingest_query(query: IngestionQuery, output_format: str = "text") -> Tuple[str, str, str]:
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
    Tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.

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

        if output_format == "jsonl":
            content = _gather_file_contents_jsonl(file_node)
            summary = f"Processed 1 file into JSONL format."
            return summary, "", content
        return format_node(file_node, query)

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

    if output_format == "jsonl":
        content = _gather_file_contents_jsonl(root_node)
        summary = f"Processed {stats.total_files} files into JSONL format."
        tree = ""
        return summary, tree, content

    return format_node(root_node, query)


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

    config = GitingestConfig(**config_section)

    if not config.ignore_patterns:
        return

    ignore_patterns = set(config.ignore_patterns)

    if query.ignore_patterns is None:
        query.ignore_patterns = ignore_patterns
    else:
        query.ignore_patterns.update(ignore_patterns)

    return


def _process_node(
    node: FileSystemNode,
    query: IngestionQuery,
    stats: FileSystemStats,
) -> bool:
    """
    Process a file or directory item within a directory using iterative BFS.

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
    from collections import deque
    from gitingest.utils.exceptions import LimitExceededError
    
    # Queue for BFS: (current_node, parent_node)
    queue = deque()
    queue.append((node, None))
    
    try:
        while queue:
            current_node, parent = queue.popleft()
            
            # Process current node
            if limit_exceeded(stats, current_node.depth):
                raise LimitExceededError("Directory depth limit exceeded")
                
            for sub_path in current_node.path.iterdir():
                try:
                    if query.ignore_patterns and _should_exclude(sub_path, query.local_path, query.ignore_patterns):
                        continue
                        
                    if query.include_patterns and not _should_include(sub_path, query.local_path, query.include_patterns):
                        continue
                        
                    if sub_path.is_symlink():
                        _process_symlink(path=sub_path, parent_node=current_node, stats=stats, local_path=query.local_path)
                    elif sub_path.is_file():
                        _process_file(path=sub_path, parent_node=current_node, stats=stats, local_path=query.local_path)
                    elif sub_path.is_dir():
                        child = FileSystemNode(
                            name=sub_path.name,
                            type=FileSystemNodeType.DIRECTORY,
                            path_str=str(sub_path.relative_to(query.local_path)),
                            path=sub_path,
                            depth=current_node.depth + 1,
                        )
                        current_node.children.append(child)
                        queue.append((child, current_node))
                    else:
                        print(f"Warning: {sub_path} is an unknown file type, skipping")
                except OSError as e:
                    print(f"Warning: Could not process {sub_path}: {str(e)}")
                    
            current_node.sort_children()
            
            # Update parent stats after processing current node
            if parent:
                parent.size += current_node.size
                parent.file_count += current_node.file_count
                parent.dir_count += 1 + current_node.dir_count
                
    except LimitExceededError:
        return True
        
    return False


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
        print(f"Maximum total size limit ({MAX_TOTAL_SIZE_BYTES/1024/1024:.1f}MB) reached")
        return True  # TODO: end recursion

    return False


def _walk_serial(root: Path, fn):
    """Yield items from ``fn`` for each file under ``root`` serially."""
    for p in root.rglob("*"):
        if p.is_file():
            yield from fn(p)
            time.sleep(0.003)


def ingest_directory_chunks(local_repo_root: Path, parallel: bool = False, incremental: bool = False):
    """Yield file chunks for all files under a directory.

    Parameters
    ----------
    local_repo_root : Path
        Directory to scan.
    parallel : bool, optional
        Use multithreaded walking if ``True``.
    incremental : bool, optional
        Use a disk cache to skip unchanged files.

    Yields
    ------
    dict
        Serialized chunk dictionaries.
    """
    cache = ChunkCache() if incremental else None

    def _ingest_single_path(path: Path):
        if cache:
            cached = cache.get(path)
            if cached:
                return cached
        chunks = chunk_file(path)
        for c in chunks:
            c.text = redact_secrets(c.text)
        data = [c.__dict__ for c in chunks]
        if cache:
            cache.set(path, data)
        return data

    walker = walk_parallel if parallel else _walk_serial
    if parallel:
        workers = max(4, (os.cpu_count() or 1) * 4)
        yield from walker(local_repo_root, _ingest_single_path, max_workers=workers)
    else:
        yield from walker(local_repo_root, _ingest_single_path)
    if cache:
        cache.flush()


def _ingest_single_path(path: Path):
    """Return chunks for a single path."""
    chunks = chunk_file(path)
    for c in chunks:
        c.text = redact_secrets(c.text)
    return chunks
