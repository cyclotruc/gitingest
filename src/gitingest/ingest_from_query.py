import os
from fnmatch import fnmatch
from typing import Any

import tiktoken

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DIRECTORY_DEPTH = 20  # Maximum depth of directory traversal
MAX_FILES = 10_000  # Maximum number of files to process
MAX_TOTAL_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


def _should_include(path: str, base_path: str, include_patterns: list[str]) -> bool:
    """
    Determines if the given file or directory path matches any of the include patterns.

    This function checks whether the relative path of a file or directory matches
    any of the specified patterns. If a match is found, it returns `True`, indicating
    that the file or directory should be included in further processing.

    Parameters
    ----------
    path : str
        The absolute path of the file or directory to check.
    base_path : str
        The base directory from which the relative path is calculated.
    include_patterns : list[str]
        A list of patterns to check against the relative path.

    Returns
    -------
    bool
        `True` if the path matches any of the include patterns, `False` otherwise.
    """
    rel_path = path.replace(base_path, "").lstrip(os.sep)
    include = False
    for pattern in include_patterns:
        if fnmatch(rel_path, pattern):
            include = True
    return include


def _should_exclude(path: str, base_path: str, ignore_patterns: list[str]) -> bool:
    """
    Determines if the given file or directory path matches any of the ignore patterns.

    This function checks whether the relative path of a file or directory matches
    any of the specified ignore patterns. If a match is found, it returns `True`, indicating
    that the file or directory should be excluded from further processing.

    Parameters
    ----------
    path : str
        The absolute path of the file or directory to check.
    base_path : str
        The base directory from which the relative path is calculated.
    ignore_patterns : list[str]
        A list of patterns to check against the relative path.

    Returns
    -------
    bool
        `True` if the path matches any of the ignore patterns, `False` otherwise.
    """
    rel_path = path.replace(base_path, "").lstrip(os.sep)
    for pattern in ignore_patterns:
        if pattern and fnmatch(rel_path, pattern):
            return True
    return False


def _is_safe_symlink(symlink_path: str, base_path: str) -> bool:
    """
    Check if a symlink points to a location within the base directory.

    This function resolves the target of a symlink and ensures it is within the specified
    base directory, returning `True` if it is safe, or `False` if the symlink points outside
    the base directory.

    Parameters
    ----------
    symlink_path : str
        The path of the symlink to check.
    base_path : str
        The base directory to ensure the symlink points within.

    Returns
    -------
    bool
        `True` if the symlink points within the base directory, `False` otherwise.
    """
    try:
        target_path = os.path.realpath(symlink_path)
        base_path = os.path.realpath(base_path)
        return os.path.commonpath([target_path, base_path]) == base_path
    except (OSError, ValueError):
        # If there's any error resolving the paths, consider it unsafe
        return False


def _is_text_file(file_path: str) -> bool:
    """
    Determine if a file is likely a text file based on its content.

    This function attempts to read the first 1024 bytes of a file and checks for the presence
    of non-text characters. It returns `True` if the file is determined to be a text file,
    otherwise returns `False`.

    Parameters
    ----------
    file_path : str
        The path to the file to check.

    Returns
    -------
    bool
        `True` if the file is likely a text file, `False` otherwise.
    """
    try:
        with open(file_path, "rb") as file:
            chunk = file.read(1024)
        return not bool(chunk.translate(None, bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))))
    except OSError:
        return False


def _read_file_content(file_path: str) -> str:
    """
    Reads the content of a file.

    This function attempts to open a file and read its contents using UTF-8 encoding.
    If an error occurs during reading (e.g., file is not found or permission error),
    it returns an error message.

    Parameters
    ----------
    file_path : str
        The path to the file to read.

    Returns
    -------
    str
        The content of the file, or an error message if the file could not be read.
    """
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def _sort_children(children: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort children nodes with:
    1. README.md first
    2. Regular files (not starting with dot)
    3. Hidden files (starting with dot)
    4. Regular directories (not starting with dot)
    5. Hidden directories (starting with dot)
    All groups are sorted alphanumerically within themselves.

    Parameters
    ----------
    children : list[dict[str, Any]]
        List of file and directory nodes to sort.

    Returns
    -------
    list[dict[str, Any]]
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
    path: str,
    query: dict[str, Any],
    seen_paths: set[str] | None = None,
    depth: int = 0,
    stats: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    """
    Recursively analyze a directory and its contents with safety limits.

    This function scans a directory and its subdirectories up to a specified depth. It checks
    for any file or directory that should be included or excluded based on the provided patterns
    and limits. It also tracks the number of files and total size processed.

    Parameters
    ----------
    path : str
        The path of the directory to scan.
    query : dict[str, Any]
        A dictionary containing the query parameters, such as include and ignore patterns.
    seen_paths : set[str] | None, optional
        A set to track already visited paths, by default None.
    depth : int, optional
        The current depth of directory traversal, by default 0.
    stats : dict[str, int] | None, optional
        A dictionary to track statistics such as total file count and size, by default None.

    Returns
    -------
    dict[str, Any] | None
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

    real_path = os.path.realpath(path)
    if real_path in seen_paths:
        print(f"Skipping already visited path: {path}")
        return None

    seen_paths.add(real_path)

    result = {
        "name": os.path.basename(path),
        "type": "directory",
        "size": 0,
        "children": [],
        "file_count": 0,
        "dir_count": 0,
        "path": path,
        "ignore_content": False,
    }

    ignore_patterns = query["ignore_patterns"]
    base_path = query["local_path"]
    include_patterns = query["include_patterns"]

    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)

            if _should_exclude(item_path, base_path, ignore_patterns):
                continue

            is_file = os.path.isfile(item_path)
            if is_file and query["include_patterns"]:
                if not _should_include(item_path, base_path, include_patterns):
                    result["ignore_content"] = True
                    continue

            # Handle symlinks
            if os.path.islink(item_path):
                if not _is_safe_symlink(item_path, base_path):
                    print(f"Skipping symlink that points outside base directory: {item_path}")
                    continue
                real_path = os.path.realpath(item_path)
                if real_path in seen_paths:
                    print(f"Skipping already visited symlink target: {item_path}")
                    continue

                if os.path.isfile(real_path):
                    file_size = os.path.getsize(real_path)
                    if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
                        print(f"Skipping file {item_path}: would exceed total size limit")
                        continue

                    stats["total_files"] += 1
                    stats["total_size"] += file_size

                    if stats["total_files"] > MAX_FILES:
                        print(f"Maximum file limit ({MAX_FILES}) reached")
                        return result

                    is_text = _is_text_file(real_path)
                    content = _read_file_content(real_path) if is_text else "[Non-text file]"

                    child = {
                        "name": item,
                        "type": "file",
                        "size": file_size,
                        "content": content,
                        "path": item_path,
                    }
                    result["children"].append(child)
                    result["size"] += file_size
                    result["file_count"] += 1

                elif os.path.isdir(real_path):
                    subdir = _scan_directory(
                        path=real_path,
                        query=query,
                        seen_paths=seen_paths,
                        depth=depth + 1,
                        stats=stats,
                    )
                    if subdir and (not include_patterns or subdir["file_count"] > 0):
                        subdir["name"] = item
                        subdir["path"] = item_path
                        result["children"].append(subdir)
                        result["size"] += subdir["size"]
                        result["file_count"] += subdir["file_count"]
                        result["dir_count"] += 1 + subdir["dir_count"]
                continue

            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
                    print(f"Skipping file {item_path}: would exceed total size limit")
                    continue

                stats["total_files"] += 1
                stats["total_size"] += file_size

                if stats["total_files"] > MAX_FILES:
                    print(f"Maximum file limit ({MAX_FILES}) reached")
                    return result

                is_text = _is_text_file(item_path)
                content = _read_file_content(item_path) if is_text else "[Non-text file]"

                child = {
                    "name": item,
                    "type": "file",
                    "size": file_size,
                    "content": content,
                    "path": item_path,
                }
                result["children"].append(child)
                result["size"] += file_size
                result["file_count"] += 1

            elif os.path.isdir(item_path):
                subdir = _scan_directory(
                    path=item_path,
                    query=query,
                    seen_paths=seen_paths,
                    depth=depth + 1,
                    stats=stats,
                )
                if subdir and (not include_patterns or subdir["file_count"] > 0):
                    result["children"].append(subdir)
                    result["size"] += subdir["size"]
                    result["file_count"] += subdir["file_count"]
                    result["dir_count"] += 1 + subdir["dir_count"]

        result["children"] = _sort_children(result["children"])
        return result

    except PermissionError:
        print(f"Permission denied: {path}")

    return result


def _extract_files_content(
    query: dict[str, Any],
    node: dict[str, Any],
    max_file_size: int,
    files: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Recursively collect all text files with their contents.

    This function traverses the directory tree and extracts the contents of all text files
    into a list, ignoring non-text files or files that exceed the specified size limit.

    Parameters
    ----------
    query : dict[str, Any]
        A dictionary containing the query parameters, including the base path of the repository.
    node : dict[str, Any]
        The current directory or file node being processed.
    max_file_size : int
        The maximum file size in bytes for which content should be extracted.
    files : list[dict[str, Any]] | None, optional
        A list to collect the extracted files' information, by default None.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries, each containing the path, content (or `None` if too large), and size of each file.
    """
    if files is None:
        files = []

    if node["type"] == "file" and node["content"] != "[Non-text file]":
        content = node["content"]
        if node["size"] > max_file_size:
            content = None

        files.append(
            {
                "path": node["path"].replace(query["local_path"], ""),
                "content": content,
                "size": node["size"],
            },
        )
    elif node["type"] == "directory":
        for child in node["children"]:
            _extract_files_content(query=query, node=child, max_file_size=max_file_size, files=files)

    return files


def _create_file_content_string(files: list[dict[str, Any]]) -> str:
    """
    Create a formatted string of file contents with separators.

    This function takes a list of files and generates a formatted string where each file’s
    content is separated by a divider.

    Parameters
    ----------
    files : list[dict[str, Any]]
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
        output += f"File: {file['path']}\n"
        output += separator
        output += f"{file['content']}\n\n"

    return output


def _create_summary_string(query: dict[str, Any], nodes: dict[str, Any]) -> str:
    """
    Create a summary string with file counts and content size.

    This function generates a summary of the repository's contents, including the number
    of files analyzed, the total content size, and other relevant details based on the query parameters.

    Parameters
    ----------
    query : dict[str, Any]
        A dictionary containing query parameters like repository name, commit, branch, and subpath.
    nodes : dict[str, Any]
        A dictionary representing the directory structure, including file and directory counts.

    Returns
    -------
    str
        A summary string containing details such as the repository name, file count, and other query-specific information.
    """
    if "user_name" in query:
        summary = f"Repository: {query['user_name']}/{query['repo_name']}\n"
    else:
        summary = f"Repository: {query['slug']}\n"

    summary += f"Files analyzed: {nodes['file_count']}\n"

    if "subpath" in query and query["subpath"] != "/":
        summary += f"Subpath: {query['subpath']}\n"
    if "commit" in query and query["commit"]:
        summary += f"Commit: {query['commit']}\n"
    elif "branch" in query and query["branch"] != "main" and query["branch"] != "master" and query["branch"]:
        summary += f"Branch: {query['branch']}\n"

    return summary


def _create_tree_structure(query: dict[str, Any], node: dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
    """
    Create a tree-like string representation of the file structure.

    This function generates a string representation of the directory structure, formatted
    as a tree with appropriate indentation for nested directories and files.

    Parameters
    ----------
    query : dict[str, Any]
        A dictionary containing query parameters like repository name and subpath.
    node : dict[str, Any]
        The current directory or file node being processed.
    prefix : str, optional
        A string used for indentation and formatting of the tree structure, by default "".
    is_last : bool, optional
        A flag indicating whether the current node is the last in its directory, by default True.

    Returns
    -------
    str
        A string representing the directory structure formatted as a tree.
    """
    tree = ""

    if not node["name"]:
        node["name"] = query["slug"]

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


def _generate_token_string(context_string: str) -> str | None:
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
    str | None
        The formatted number of tokens as a string (e.g., '1.2k', '1.2M'), or `None` if an error occurs.
    """
    formatted_tokens = ""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        total_tokens = len(encoding.encode(context_string, disallowed_special=()))

    except Exception as e:
        print(e)
        return None

    if total_tokens > 1_000_000:
        formatted_tokens = f"{total_tokens / 1_000_000:.1f}M"
    elif total_tokens > 1_000:
        formatted_tokens = f"{total_tokens / 1_000:.1f}k"
    else:
        formatted_tokens = f"{total_tokens}"

    return formatted_tokens


def _ingest_single_file(path: str, query: dict[str, Any]) -> tuple[str, str, str]:
    """
    Ingest a single file and return its summary, directory structure, and content.

    This function reads a file, generates a summary of its contents, and returns the content
    along with its directory structure and token estimation.

    Parameters
    ----------
    path : str
        The path of the file to ingest.
    query : dict[str, Any]
        A dictionary containing query parameters, such as the maximum file size.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing the summary, directory structure, and file content.

    Raises
    ------
    ValueError
        If the specified path is not a file or if the file is not a text file.
    """
    if not os.path.isfile(path):
        raise ValueError(f"Path {path} is not a file")

    file_size = os.path.getsize(path)
    is_text = _is_text_file(path)
    if not is_text:
        raise ValueError(f"File {path} is not a text file")

    content = _read_file_content(path)
    if file_size > query["max_file_size"]:
        content = "[Content ignored: file too large]"

    file_info = {
        "path": path.replace(query["local_path"], ""),
        "content": content,
        "size": file_size,
    }

    summary = (
        f"Repository: {query['user_name']}/{query['repo_name']}\n"
        f"File: {os.path.basename(path)}\n"
        f"Size: {file_size:,} bytes\n"
        f"Lines: {len(content.splitlines()):,}\n"
    )

    files_content = _create_file_content_string([file_info])
    tree = "Directory structure:\n└── " + os.path.basename(path)

    formatted_tokens = _generate_token_string(files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def _ingest_directory(path: str, query: dict[str, Any]) -> tuple[str, str, str]:
    """
    Ingest an entire directory and return its summary, directory structure, and file contents.

    This function processes a directory, extracts its contents, and generates a summary,
    directory structure, and file content. It recursively processes subdirectories as well.

    Parameters
    ----------
    path : str
        The path of the directory to ingest.
    query : dict[str, Any]
        A dictionary containing query parameters, including maximum file size.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.

    Raises
    ------
    ValueError
        If no files are found in the directory.
    """
    nodes = _scan_directory(path=path, query=query)
    if not nodes:
        raise ValueError(f"No files found in {path}")
    files = _extract_files_content(query=query, node=nodes, max_file_size=query["max_file_size"])
    summary = _create_summary_string(query, nodes)
    tree = "Directory structure:\n" + _create_tree_structure(query, nodes)
    files_content = _create_file_content_string(files)

    formatted_tokens = _generate_token_string(tree + files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def ingest_from_query(query: dict[str, Any]) -> tuple[str, str, str]:
    """
    Main entry point for analyzing a codebase directory or single file.

    This function processes a file or directory based on the provided query, extracting its contents
    and generating a summary, directory structure, and file content, along with token estimations.

    Parameters
    ----------
    query : dict[str, Any]
        A dictionary containing parameters like local path, subpath, file type, etc.

    Returns
    -------
    tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.

    Raises
    ------
    ValueError
        If the specified path cannot be found or if the file is not a text file.
    """
    path = f"{query['local_path']}{query['subpath']}"
    if not os.path.exists(path):
        raise ValueError(f"{query['slug']} cannot be found")

    if query.get("type") == "blob":
        return _ingest_single_file(path, query)

    return _ingest_directory(path, query)
