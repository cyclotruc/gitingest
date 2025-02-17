""" Functions to ingest and analyze a codebase directory or single file. """

import locale
import os
import platform
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import tiktoken

from gitingest.config import MAX_DIRECTORY_DEPTH, MAX_FILES, MAX_TOTAL_SIZE_BYTES
from gitingest.exceptions import (
    AlreadyVisitedError,
    InvalidNotebookError,
    MaxFileSizeReachedError,
    MaxFilesReachedError,
)
from gitingest.notebook_utils import process_notebook
from gitingest.query_parser import ParsedQuery

try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "C")


def _normalize_path(path: Path) -> Path:
    """
    Normalize path for cross-platform compatibility.

    Parameters
    ----------
    path : Path
        The Path object to normalize.

    Returns
    -------
    Path
        The normalized path with platform-specific separators and resolved components.
    """
    return Path(os.path.normpath(str(path)))


def _normalize_path_str(path: Union[Path, str]) -> str:
    """
    Convert path to string with forward slashes for consistent output.

    Parameters
    ----------
    path : str | Path
        The path to convert, can be string or Path object.

    Returns
    -------
    str
        The normalized path string with forward slashes as separators.
    """
    return str(path).replace(os.sep, "/")


def _get_encoding_list() -> List[str]:
    """
    Get list of encodings to try, prioritized for the current platform.

    Returns
    -------
    List[str]
        List of encoding names to try in priority order, starting with the
        platform's default encoding followed by common fallback encodings.
    """
    encodings = ["utf-8", "utf-8-sig", "latin"]
    if platform.system() == "Windows":
        encodings.extend(["cp1252", "iso-8859-1"])
    return encodings + [locale.getpreferredencoding()]


def _should_include(path: Path, base_path: Path, include_patterns: Set[str]) -> bool:
    """
    Determine if the given file or directory path matches any of the include patterns.

    This function checks whether the relative path of a file or directory matches any of the specified patterns. If a
    match is found, it returns `True`, indicating that the file or directory should be included in further processing.

    Parameters
    ----------
    path : Path
        The absolute path of the file or directory to check.
    base_path : Path
        The base directory from which the relative path is calculated.
    include_patterns : Set[str]
        A set of patterns to check against the relative path.

    Returns
    -------
    bool
        `True` if the path matches any of the include patterns, `False` otherwise.
    """
    try:
        rel_path = path.relative_to(base_path)
    except ValueError:
        # If path is not under base_path at all
        return False

    rel_str = str(rel_path)
    for pattern in include_patterns:
        if fnmatch(rel_str, pattern):
            return True
    return False


def _should_exclude(path: Path, base_path: Path, ignore_patterns: Set[str]) -> bool:
    """
    Determine if the given file or directory path matches any of the ignore patterns.

    This function checks whether the relative path of a file or directory matches
    any of the specified ignore patterns. If a match is found, it returns `True`, indicating
    that the file or directory should be excluded from further processing.

    Parameters
    ----------
    path : Path
        The absolute path of the file or directory to check.
    base_path : Path
        The base directory from which the relative path is calculated.
    ignore_patterns : Set[str]
        A set of patterns to check against the relative path.

    Returns
    -------
    bool
        `True` if the path matches any of the ignore patterns, `False` otherwise.
    """
    try:
        rel_path = path.relative_to(base_path)
    except ValueError:
        # If path is not under base_path at all
        return True

    rel_str = str(rel_path)
    for pattern in ignore_patterns:
        if pattern and fnmatch(rel_str, pattern):
            return True
    return False


def _is_safe_symlink(symlink_path: Path, base_path: Path) -> bool:
    """
    Check if a symlink points to a location within the base directory.

    This function resolves the target of a symlink and ensures it is within the specified
    base directory, returning `True` if it is safe, or `False` if the symlink points outside
    the base directory.

    Parameters
    ----------
    symlink_path : Path
        The path of the symlink to check.
    base_path : Path
        The base directory to ensure the symlink points within.

    Returns
    -------
    bool
        `True` if the symlink points within the base directory, `False` otherwise.
    """
    try:
        if platform.system() == "Windows":
            if not os.path.islink(str(symlink_path)):
                return False

        target_path = _normalize_path(symlink_path.resolve())
        base_resolved = _normalize_path(base_path.resolve())

        return base_resolved in target_path.parents or target_path == base_resolved
    except (OSError, ValueError):
        # If there's any error resolving the paths, consider it unsafe
        return False


def _is_text_file(file_path: Path) -> bool:
    """
    Determine if a file is likely a text file based on its content.

    This function attempts to read the first 1024 bytes of a file and checks for the presence
    of non-text characters. It returns `True` if the file is determined to be a text file,
    otherwise returns `False`.

    Parameters
    ----------
    file_path : Path
        The path to the file to check.

    Returns
    -------
    bool
        `True` if the file is likely a text file, `False` otherwise.
    """
    try:
        with file_path.open("rb") as file:
            chunk = file.read(1024)
        return not bool(chunk.translate(None, bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))))
    except OSError:
        return False


def _read_file_content(file_path: Path) -> str:
    """
    Read the content of a file.

    This function attempts to open a file and read its contents using UTF-8 encoding.
    If an error occurs during reading (e.g., file is not found or permission error),
    it returns an error message.

    Parameters
    ----------
    file_path : Path
        The path to the file to read.

    Returns
    -------
    str
        The content of the file, or an error message if the file could not be read.
    """
    try:
        if file_path.suffix == ".ipynb":
            try:
                return process_notebook(file_path)
            except Exception as e:
                return f"Error processing notebook: {e}"

        for encoding in _get_encoding_list():
            try:
                with open(file_path, encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except OSError as e:
                return f"Error reading file: {e}"

        return "Error: Unable to decode file with available encodings"

    except (OSError, InvalidNotebookError) as e:
        return f"Error reading file: {e}"


def _sort_children(children: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort the children nodes of a directory according to a specific order.

    Order of sorting:
    1. README.md first
    2. Regular files (not starting with dot)
    3. Hidden files (starting with dot)
    4. Regular directories (not starting with dot)
    5. Hidden directories (starting with dot)
    All groups are sorted alphanumerically within themselves.

    Parameters
    ----------
    children : List[Dict[str, Any]]
        List of file and directory nodes to sort.

    Returns
    -------
    List[Dict[str, Any]]
        Sorted list according to the specified order.
    """
    # Separate files and directories
    files = [child for child in children if child["type"] == "file"]
    directories = [child for child in children if child["type"] == "directory"]

    # Find README.md
    readme_files = [f for f in files if f["name"].lower() == "readme.md"]
    other_files = [f for f in files if f["name"].lower() != "readme.md"]

    # Separate hidden and regular files/directories
    regular_files = [f for f in other_files if not f["name"].startswith(".")]
    hidden_files = [f for f in other_files if f["name"].startswith(".")]
    regular_dirs = [d for d in directories if not d["name"].startswith(".")]
    hidden_dirs = [d for d in directories if d["name"].startswith(".")]

    # Sort each group alphanumerically
    regular_files.sort(key=lambda x: x["name"])
    hidden_files.sort(key=lambda x: x["name"])
    regular_dirs.sort(key=lambda x: x["name"])
    hidden_dirs.sort(key=lambda x: x["name"])

    # Combine all groups in the desired order
    return readme_files + regular_files + hidden_files + regular_dirs + hidden_dirs


def _scan_directory(
    path: Path,
    query: ParsedQuery,
    seen_paths: Optional[Set[Path]] = None,
    depth: int = 0,
    stats: Optional[Dict[str, int]] = None,
) -> Optional[Dict[str, Any]]:
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
    Dict[str, Any] | None
        A dictionary representing the directory structure and contents, or `None` if limits are reached.
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

    result = {
        "name": path.name,
        "type": "directory",
        "size": 0,
        "children": [],
        "file_count": 0,
        "dir_count": 0,
        "path": str(path),
        "ignore_content": False,
    }

    try:
        for item in path.iterdir():
            _process_item(item=item, query=query, result=result, seen_paths=seen_paths, stats=stats, depth=depth)
    except MaxFilesReachedError:
        print(f"Maximum file limit ({MAX_FILES}) reached.")
    except PermissionError:
        print(f"Permission denied: {path}.")

    result["children"] = _sort_children(result["children"])
    return result


def _process_symlink(
    item: Path,
    query: ParsedQuery,
    result: Dict[str, Any],
    seen_paths: Set[Path],
    stats: Dict[str, int],
    depth: int,
) -> None:
    """
    Process a symlink in the file system.

    This function checks if a symlink is safe, resolves its target, and processes it accordingly.
    If the symlink is not safe, an exception is raised.

    Parameters
    ----------
    item : Path
        The full path of the symlink.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    result : Dict[str, Any]
        The dictionary to accumulate the results.
    seen_paths : Set[str]
        A set of already visited paths.
    stats : Dict[str, int]
        The dictionary to track statistics such as file count and size.
    depth : int
        The current depth in the directory traversal.

    Raises
    ------
    AlreadyVisitedError
        If the symlink has already been processed.
    MaxFileSizeReachedError
        If the file size exceeds the maximum limit.
    MaxFilesReachedError
        If the number of files exceeds the maximum limit.
    """

    if not _is_safe_symlink(item, query.local_path):
        raise AlreadyVisitedError(str(item))

    real_path = item.resolve()
    if real_path in seen_paths:
        raise AlreadyVisitedError(str(item))

    if real_path.is_file():
        file_size = real_path.stat().st_size
        if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
            raise MaxFileSizeReachedError(MAX_TOTAL_SIZE_BYTES)

        stats["total_files"] += 1
        stats["total_size"] += file_size

        if stats["total_files"] > MAX_FILES:
            print(f"Maximum file limit ({MAX_FILES}) reached")
            raise MaxFilesReachedError(MAX_FILES)

        is_text = _is_text_file(real_path)
        content = _read_file_content(real_path) if is_text else "[Non-text file]"

        child = {
            "name": item.name,
            "type": "file",
            "size": file_size,
            "content": content,
            "path": str(item),
        }
        result["children"].append(child)
        result["size"] += file_size
        result["file_count"] += 1

    elif real_path.is_dir():
        subdir = _scan_directory(
            path=real_path,
            query=query,
            seen_paths=seen_paths,
            depth=depth + 1,
            stats=stats,
        )
        if subdir and (not query.include_patterns or subdir["file_count"] > 0):
            # rename the subdir to reflect the symlink name
            subdir["name"] = item.name
            subdir["path"] = str(item)
            result["children"].append(subdir)
            result["size"] += subdir["size"]
            result["file_count"] += subdir["file_count"]
            result["dir_count"] += 1 + subdir["dir_count"]


def _process_file(item: Path, result: Dict[str, Any], stats: Dict[str, int]) -> None:
    """
    Process a file in the file system.

    This function checks the file's size, increments the statistics, and reads its content.
    If the file size exceeds the maximum allowed, it raises an error.

    Parameters
    ----------
    item : Path
        The full path of the file.
    result : Dict[str, Any]
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
    file_size = item.stat().st_size
    if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
        print(f"Skipping file {item}: would exceed total size limit")
        raise MaxFileSizeReachedError(MAX_TOTAL_SIZE_BYTES)

    stats["total_files"] += 1
    stats["total_size"] += file_size

    if stats["total_files"] > MAX_FILES:
        print(f"Maximum file limit ({MAX_FILES}) reached")
        raise MaxFilesReachedError(MAX_FILES)

    is_text = _is_text_file(item)
    content = _read_file_content(item) if is_text else "[Non-text file]"

    child = {
        "name": item.name,
        "type": "file",
        "size": file_size,
        "content": content,
        "path": str(item),
    }
    result["children"].append(child)
    result["size"] += file_size
    result["file_count"] += 1


def _process_item(
    item: Path,
    query: ParsedQuery,
    result: Dict[str, Any],
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
    item : Path
        The full path of the file or directory to process.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    result : Dict[str, Any]
        The result dictionary to accumulate processed file/directory data.
    seen_paths : Set[Path]
        A set of paths that have already been visited.
    stats : Dict[str, int]
        A dictionary of statistics like the total file count and size.
    depth : int
        The current depth of directory traversal.
    """

    if not query.ignore_patterns or _should_exclude(item, query.local_path, query.ignore_patterns):
        return

    if (
        item.is_file()
        and query.include_patterns
        and not _should_include(item, query.local_path, query.include_patterns)
    ):
        result["ignore_content"] = True
        return

    try:
        if item.is_symlink():
            _process_symlink(item=item, query=query, result=result, seen_paths=seen_paths, stats=stats, depth=depth)

        if item.is_file():
            _process_file(item=item, result=result, stats=stats)

        elif item.is_dir():
            subdir = _scan_directory(path=item, query=query, seen_paths=seen_paths, depth=depth + 1, stats=stats)
            if subdir and (not query.include_patterns or subdir["file_count"] > 0):
                result["children"].append(subdir)
                result["size"] += subdir["size"]
                result["file_count"] += subdir["file_count"]
                result["dir_count"] += 1 + subdir["dir_count"]

    except (MaxFileSizeReachedError, AlreadyVisitedError) as e:
        print(e)


def _extract_files_content(
    query: ParsedQuery,
    node: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Recursively collect all text files with their contents.

    This function traverses the directory tree and extracts the contents of all text files
    into a list, ignoring non-text files or files that exceed the specified size limit.

    Parameters
    ----------
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    node : Dict[str, Any]
        The current directory or file node being processed.
    files : List[Dict[str, Any]] | None, optional
        A list to collect the extracted files' information, by default None.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each containing the path, content (or `None` if too large), and size of each file.
    """
    if files is None:
        files = []

    if node["type"] == "file" and node["content"] != "[Non-text file]":
        if node["size"] > query.max_file_size:
            content = None
        else:
            content = node["content"]

        relative_path = Path(node["path"]).relative_to(query.local_path)
        # Store paths with forward slashes
        files.append(
            {
                "path": _normalize_path_str(relative_path),
                "content": content,
                "size": node["size"],
            },
        )
    elif node["type"] == "directory":
        for child in node["children"]:
            _extract_files_content(query=query, node=child, files=files)

    return files


def _create_file_content_string(files: List[Dict[str, Any]]) -> str:
    """
    Create a formatted string of file contents with separators.

    This function takes a list of files and generates a formatted string where each file's
    content is separated by a divider.

    Parameters
    ----------
    files : List[Dict[str, Any]]
        A list of dictionaries containing file information, including the path and content.

    Returns
    -------
    str
        A formatted string representing the contents of all the files with appropriate separators.
    """
    output = ""
    separator = "=" * 48 + "\n"

    # Then add all other files in their original order
    for file in files:
        if not file["content"]:
            continue

        output += separator
        # Use forward slashes in output paths
        output += f"File: {_normalize_path_str(file['path'])}\n"
        output += separator
        output += f"{file['content']}\n\n"

    return output


def _create_summary_string(query: ParsedQuery, nodes: Dict[str, Any]) -> str:
    """
    Create a summary string with file counts and content size.

    This function generates a summary of the repository's contents, including the number
    of files analyzed, the total content size, and other relevant details based on the query parameters.

    Parameters
    ----------
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    nodes : Dict[str, Any]
        Dictionary representing the directory structure, including file and directory counts.

    Returns
    -------
    str
        Summary string containing details such as repository name, file count, and other query-specific information.
    """
    if query.user_name:
        summary = f"Repository: {query.user_name}/{query.repo_name}\n"
    else:
        summary = f"Repository: {query.slug}\n"

    summary += f"Files analyzed: {nodes['file_count']}\n"

    if query.subpath != "/":
        summary += f"Subpath: {query.subpath}\n"
    if query.commit:
        summary += f"Commit: {query.commit}\n"
    elif query.branch and query.branch not in ("main", "master"):
        summary += f"Branch: {query.branch}\n"

    return summary


def _create_tree_structure(query: ParsedQuery, node: Dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
    """
    Create a tree-like string representation of the file structure.

    This function generates a string representation of the directory structure, formatted
    as a tree with appropriate indentation for nested directories and files.

    Parameters
    ----------
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    node : Dict[str, Any]
        The current directory or file node being processed.
    prefix : str
        A string used for indentation and formatting of the tree structure, by default "".
    is_last : bool
        A flag indicating whether the current node is the last in its directory, by default True.

    Returns
    -------
    str
        A string representing the directory structure formatted as a tree.
    """
    tree = ""

    if not node["name"]:
        node["name"] = query.slug

    if node["name"]:
        current_prefix = "└── " if is_last else "├── "
        name = node["name"] + "/" if node["type"] == "directory" else node["name"]
        tree += prefix + current_prefix + name + "\n"

    if node["type"] == "directory":
        # Adjust prefix only if we added a node name
        new_prefix = prefix + ("    " if is_last else "│   ") if node["name"] else prefix
        children = node["children"]
        for i, child in enumerate(children):
            tree += _create_tree_structure(query, child, new_prefix, i == len(children) - 1)

    return tree


def _generate_token_string(context_string: str) -> Optional[str]:
    """
    Return the number of tokens in a text string.

    This function estimates the number of tokens in a given text string using the `tiktoken`
    library. It returns the number of tokens in a human-readable format (e.g., '1.2k', '1.2M').

    Parameters
    ----------
    context_string : str
        The text string for which the token count is to be estimated.

    Returns
    -------
    str, optional
        The formatted number of tokens as a string (e.g., '1.2k', '1.2M'), or `None` if an error occurs.
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        total_tokens = len(encoding.encode(context_string, disallowed_special=()))
    except (ValueError, UnicodeEncodeError) as e:
        print(e)
        return None

    if total_tokens > 1_000_000:
        return f"{total_tokens / 1_000_000:.1f}M"

    if total_tokens > 1_000:
        return f"{total_tokens / 1_000:.1f}k"

    return str(total_tokens)


def _ingest_single_file(path: Path, query: ParsedQuery) -> Tuple[str, str, str]:
    """
    Ingest a single file and return its summary, directory structure, and content.

    This function reads a file, generates a summary of its contents, and returns the content
    along with its directory structure and token estimation.

    Parameters
    ----------
    path : Path
        The path of the file to ingest.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    Tuple[str, str, str]
        A tuple containing the summary, directory structure, and file content.

    Raises
    ------
    ValueError
        If the specified path is not a file or if the file is not a text file.
    """
    if not path.is_file():
        raise ValueError(f"Path {path} is not a file")

    if not _is_text_file(path):
        raise ValueError(f"File {path} is not a text file")

    file_size = path.stat().st_size
    if file_size > query.max_file_size:
        content = "[Content ignored: file too large]"
    else:
        content = _read_file_content(path)

    relative_path = path.relative_to(query.local_path)

    file_info = {
        "path": str(relative_path),
        "content": content,
        "size": file_size,
    }

    summary = (
        f"Repository: {query.user_name}/{query.repo_name}\n"
        f"File: {path.name}\n"
        f"Size: {file_size:,} bytes\n"
        f"Lines: {len(content.splitlines()):,}\n"
    )

    files_content = _create_file_content_string([file_info])
    tree = "Directory structure:\n└── " + path.name

    formatted_tokens = _generate_token_string(files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def _ingest_directory(path: Path, query: ParsedQuery) -> Tuple[str, str, str]:
    """
    Ingest an entire directory and return its summary, directory structure, and file contents.

    This function processes a directory, extracts its contents, and generates a summary,
    directory structure, and file content. It recursively processes subdirectories as well.

    Parameters
    ----------
    path : Path
        The path of the directory to ingest.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    Tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.

    Raises
    ------
    ValueError
        If no files are found in the directory.
    """
    nodes = _scan_directory(path=path, query=query)
    if not nodes:
        raise ValueError(f"No files found in {path}")

    files = _extract_files_content(query=query, node=nodes)
    summary = _create_summary_string(query, nodes)
    tree = "Directory structure:\n" + _create_tree_structure(query, nodes)
    files_content = _create_file_content_string(files)

    formatted_tokens = _generate_token_string(tree + files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def run_ingest_query(query: ParsedQuery) -> Tuple[str, str, str]:
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
    subpath = _normalize_path(Path(query.subpath.strip("/"))).as_posix()
    path = _normalize_path(query.local_path / subpath)

    if not path.exists():
        raise ValueError(f"{query.slug} cannot be found")

    if query.type and query.type == "blob":
        return _ingest_single_file(path, query)

    return _ingest_directory(path, query)
