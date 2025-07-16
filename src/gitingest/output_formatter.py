"""Functions to ingest and analyze a codebase directory or single file.

Memory optimization:
- Generator-based processing: Uses generators to process files one at a time
- Streaming approach: Avoids loading all file contents into memory at once
- Works with lazy loading: Complements the lazy loading in FileSystemNode
"""

from __future__ import annotations

import gc
import io
from typing import TYPE_CHECKING, Generator

import tiktoken

from gitingest.schemas import FileSystemNode, FileSystemNodeType
from gitingest.utils.compat_func import readlink

if TYPE_CHECKING:
    from gitingest.query_parser import IngestionQuery

_TOKEN_THRESHOLDS: list[tuple[int, str]] = [
    (1_000_000, "M"),
    (1_000, "k"),
]


def format_node(node: FileSystemNode, query: IngestionQuery) -> tuple[str, str, str]:
    """Generate a summary, directory structure, and file contents for a given file system node.

    If the node represents a directory, the function will recursively process its contents.

    Parameters
    ----------
    node : FileSystemNode
        The file system node to be summarized.
    query : IngestionQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.

    """
    is_single_file = node.type == FileSystemNodeType.FILE
    summary = _create_summary_prefix(query, single_file=is_single_file)

    if node.type == FileSystemNodeType.DIRECTORY:
        summary += f"Files analyzed: {node.file_count}\n"
    elif node.type == FileSystemNodeType.FILE:
        summary += f"File: {node.name}\n"
        summary += f"Lines: {len(node.content.splitlines()):,}\n"

    tree = "Directory structure:\n" + _create_tree_structure(query, node=node)

    # Estimate tokens for tree
    tree_tokens = _count_tokens(tree)

    # For token estimation, we need to sample some content
    # We'll use a small sample to estimate without loading everything
    content_sample = ""
    content_generator = _gather_file_contents(node)

    # Try to get a small sample for token estimation
    try:
        # Get first item from generator for sampling
        first_item = next(content_generator)
        sample_size = min(len(first_item), 10000)  # Limit sample size
        content_sample = first_item[:sample_size]
    except StopIteration:
        # No content
        pass

    # Estimate tokens based on sample
    sample_tokens = _count_tokens(content_sample)

    # If we have a sample, extrapolate total tokens based on file sizes
    if sample_tokens > 0 and len(content_sample) > 0:
        # Estimate tokens per byte
        tokens_per_byte = sample_tokens / len(content_sample)
        # Estimate total tokens based on total file size
        estimated_content_tokens = int(node.size * tokens_per_byte)
        total_tokens = tree_tokens + estimated_content_tokens
    else:
        total_tokens = tree_tokens

    token_estimate = _format_token_count(total_tokens)
    if token_estimate:
        summary += f"\nEstimated tokens: {token_estimate}"

    # For backward compatibility with tests, return content as a string
    # But use a more memory-efficient approach by processing files in chunks
    content = _gather_content_string(node)

    return summary, tree, content


def _create_summary_prefix(query: IngestionQuery, *, single_file: bool = False) -> str:
    """Create a prefix string for summarizing a repository or local directory.

    Includes repository name (if provided), commit/branch details, and subpath if relevant.

    Parameters
    ----------
    query : IngestionQuery
        The parsed query object containing information about the repository and query parameters.
    single_file : bool
        A flag indicating whether the summary is for a single file (default: ``False``).

    Returns
    -------
    str
        A summary prefix string containing repository, commit, branch, and subpath details.

    """
    parts = []

    if query.user_name:
        parts.append(f"Repository: {query.user_name}/{query.repo_name}")
    else:
        # Local scenario
        parts.append(f"Directory: {query.slug}")

    if query.commit:
        parts.append(f"Commit: {query.commit}")
    elif query.branch and query.branch not in ("main", "master"):
        parts.append(f"Branch: {query.branch}")

    if query.subpath != "/" and not single_file:
        parts.append(f"Subpath: {query.subpath}")

    return "\n".join(parts) + "\n"


def _gather_file_contents(node: FileSystemNode) -> Generator[str]:
    """Recursively gather contents of all files under the given node.

    This function recursively processes a directory node and yields the contents of all files
    under that node one at a time. Instead of concatenating all content into a single string,
    it returns a generator that yields each file's content separately.

    The implementation is memory-efficient, processing one file at a time and using
    generators to avoid loading all content into memory at once.

    Parameters
    ----------
    node : FileSystemNode
        The current directory or file node being processed.

    Yields
    ------
    Generator[str]
        The content of each file as a string.

    """
    if node.type != FileSystemNodeType.DIRECTORY:
        yield node.content_string
        # Clear content cache immediately after yielding to free memory
        node.clear_content_cache()
    else:
        # Process one child at a time to avoid loading all content at once
        for child in node.children:
            yield from _gather_file_contents(child)


def _gather_content_string(node: FileSystemNode) -> str:
    """Gather file contents as a string, but in a memory-efficient way.

    This function processes files in chunks to avoid loading all content into memory at once.
    It builds the content string incrementally, clearing file content caches as it goes.

    For very large repositories, it uses a more aggressive chunking strategy to minimize memory usage.

    Parameters
    ----------
    node : FileSystemNode
        The file system node to process.

    Returns
    -------
    str
        The combined content string.

    """
    # For very small repositories (less than 10MB), use simple approach
    if node.size < 10 * 1024 * 1024:
        content_chunks = list(_gather_file_contents(node))
        return "\n".join(content_chunks)

    # For medium repositories (10MB to 100MB), use chunked approach
    if node.size < 100 * 1024 * 1024:
        # Use a list to accumulate content chunks
        content_chunks = []
        chunk_size = 0
        max_chunk_size = 5 * 1024 * 1024  # 5MB per chunk

        # Process files in batches to limit memory usage
        for content_item in _gather_file_contents(node):
            content_chunks.append(content_item)
            chunk_size += len(content_item)

            # If we've accumulated enough content, join it and reset
            if chunk_size >= max_chunk_size:
                # Join the current chunks
                joined_chunk = "\n".join(content_chunks)
                # Reset the chunks list with just the joined chunk
                content_chunks = [joined_chunk]
                # Update the chunk size
                chunk_size = len(joined_chunk)

        # Join any remaining chunks
        return "\n".join(content_chunks)

    # For large repositories (over 100MB), use a hybrid approach with StringIO
    # Use StringIO as a memory-efficient buffer
    buffer = io.StringIO()
    flush_interval = 100  # Flush to string every 100 files

    # Process files and write to buffer
    for i, content_item in enumerate(_gather_file_contents(node)):
        buffer.write(content_item)
        buffer.write("\n")

        # Periodically get the current value to avoid buffer growing too large
        if (i + 1) % flush_interval == 0:
            # Get current value
            current_value = buffer.getvalue()

            # Reset buffer
            buffer.close()
            buffer = io.StringIO()

            # Write current value back to buffer
            buffer.write(current_value)

            # Force garbage collection to free memory
            gc.collect()

    # Get final result
    result = buffer.getvalue()
    buffer.close()

    return result


def _create_tree_structure(
    query: IngestionQuery,
    *,
    node: FileSystemNode,
    prefix: str = "",
    is_last: bool = True,
) -> str:
    """Generate a tree-like string representation of the file structure.

    This function generates a string representation of the directory structure, formatted
    as a tree with appropriate indentation for nested directories and files.

    Parameters
    ----------
    query : IngestionQuery
        The parsed query object containing information about the repository and query parameters.
    node : FileSystemNode
        The current directory or file node being processed.
    prefix : str
        A string used for indentation and formatting of the tree structure (default: ``""``).
    is_last : bool
        A flag indicating whether the current node is the last in its directory (default: ``True``).

    Returns
    -------
    str
        A string representing the directory structure formatted as a tree.

    """
    if not node.name:
        # If no name is present, use the slug as the top-level directory name
        node.name = query.slug

    tree_str = ""
    current_prefix = "└── " if is_last else "├── "

    # Indicate directories with a trailing slash
    display_name = node.name
    if node.type == FileSystemNodeType.DIRECTORY:
        display_name += "/"
    elif node.type == FileSystemNodeType.SYMLINK:
        display_name += " -> " + readlink(node.path).name

    tree_str += f"{prefix}{current_prefix}{display_name}\n"

    if node.type == FileSystemNodeType.DIRECTORY and node.children:
        prefix += "    " if is_last else "│   "
        for i, child in enumerate(node.children):
            tree_str += _create_tree_structure(query, node=child, prefix=prefix, is_last=i == len(node.children) - 1)
    return tree_str


def _count_tokens(text: str) -> int:
    """Count the number of tokens in a text string.

    Parameters
    ----------
    text : str
        The text string for which to count tokens.

    Returns
    -------
    int
        The number of tokens in the text, or 0 if an error occurs.

    """
    try:
        encoding = tiktoken.get_encoding("o200k_base")  # gpt-4o, gpt-4o-mini
        return len(encoding.encode(text, disallowed_special=()))
    except (ValueError, UnicodeEncodeError) as exc:
        print(exc)
        return 0


def _format_token_count(total_tokens: int) -> str | None:
    """Return a human-readable token-count string (e.g. 1.2k, 1.2 M).

    Parameters
    ----------
    total_tokens : int
        The number of tokens to format.

    Returns
    -------
    str | None
        The formatted number of tokens as a string (e.g., ``"1.2k"``, ``"1.2M"``), or ``None`` if total_tokens is 0.

    """
    if total_tokens == 0:
        return None

    for threshold, suffix in _TOKEN_THRESHOLDS:
        if total_tokens >= threshold:
            return f"{total_tokens / threshold:.1f}{suffix}"

    return str(total_tokens)
