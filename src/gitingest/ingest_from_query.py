import os
from fnmatch import fnmatch
from typing import Any

import tiktoken

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DIRECTORY_DEPTH = 20  # Maximum depth of directory traversal
MAX_FILES = 10_000  # Maximum number of files to process
MAX_TOTAL_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


def should_include(path: str, base_path: str, include_patterns: list[str]) -> bool:
    rel_path = path.replace(base_path, "").lstrip(os.sep)
    include = False
    for pattern in include_patterns:
        if fnmatch(rel_path, pattern):
            include = True
    return include


def should_exclude(path: str, base_path: str, ignore_patterns: list[str]) -> bool:
    rel_path = path.replace(base_path, "").lstrip(os.sep)
    for pattern in ignore_patterns:
        if pattern == "":
            continue
        if fnmatch(rel_path, pattern):
            return True
    return False


def is_safe_symlink(symlink_path: str, base_path: str) -> bool:
    """Check if a symlink points to a location within the base directory."""
    try:
        target_path = os.path.realpath(symlink_path)
        base_path = os.path.realpath(base_path)
        return os.path.commonpath([target_path, base_path]) == base_path
    except (OSError, ValueError):
        # If there's any error resolving the paths, consider it unsafe
        return False


def is_text_file(file_path: str) -> bool:
    """Determines if a file is likely a text file based on its content."""
    try:
        with open(file_path, "rb") as file:
            chunk = file.read(1024)
        return not bool(chunk.translate(None, bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))))
    except OSError:
        return False


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def scan_directory(
    path: str,
    query: dict[str, Any],
    seen_paths: set[str] | None = None,
    depth: int = 0,
    stats: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    """Recursively analyzes a directory and its contents with safety limits."""
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

            if should_exclude(item_path, base_path, ignore_patterns):
                continue

            is_file = os.path.isfile(item_path)
            if is_file and query["include_patterns"]:
                if not should_include(item_path, base_path, include_patterns):
                    result["ignore_content"] = True
                    continue

            # Handle symlinks
            if os.path.islink(item_path):
                if not is_safe_symlink(item_path, base_path):
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

                    is_text = is_text_file(real_path)
                    content = read_file_content(real_path) if is_text else "[Non-text file]"

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
                    subdir = scan_directory(
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

                is_text = is_text_file(item_path)
                content = read_file_content(item_path) if is_text else "[Non-text file]"

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
                subdir = scan_directory(
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

    except PermissionError:
        print(f"Permission denied: {path}")

    return result


def extract_files_content(
    query: dict[str, Any],
    node: dict[str, Any],
    max_file_size: int,
    files: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Recursively collects all text files with their contents."""
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
            extract_files_content(query=query, node=child, max_file_size=max_file_size, files=files)

    return files


def create_file_content_string(files: list[dict[str, Any]]) -> str:
    """Creates a formatted string of file contents with separators."""
    output = ""
    separator = "=" * 48 + "\n"

    # First add README.md if it exists
    for file in files:
        if not file["content"]:
            continue

        if file["path"].lower() == "/readme.md":
            output += separator
            output += f"File: {file['path']}\n"
            output += separator
            output += f"{file['content']}\n\n"
            break

    # Then add all other files in their original order
    for file in files:
        if not file["content"] or file["path"].lower() == "/readme.md":
            continue

        output += separator
        output += f"File: {file['path']}\n"
        output += separator
        output += f"{file['content']}\n\n"

    return output


def create_summary_string(query: dict[str, Any], nodes: dict[str, Any]) -> str:
    """Creates a summary string with file counts and content size."""
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


def create_tree_structure(query: dict[str, Any], node: dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
    """Creates a tree-like string representation of the file structure."""
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
            tree += create_tree_structure(query, child, new_prefix, i == len(children) - 1)

    return tree


def generate_token_string(context_string: str) -> str | None:
    """Returns the number of tokens in a text string."""
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


def ingest_single_file(path: str, query: dict[str, Any]) -> tuple[str, str, str]:
    if not os.path.isfile(path):
        raise ValueError(f"Path {path} is not a file")

    file_size = os.path.getsize(path)
    is_text = is_text_file(path)
    if not is_text:
        raise ValueError(f"File {path} is not a text file")

    content = read_file_content(path)
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

    files_content = create_file_content_string([file_info])
    tree = "Directory structure:\n└── " + os.path.basename(path)

    formatted_tokens = generate_token_string(files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def ingest_directory(path: str, query: dict[str, Any]) -> tuple[str, str, str]:
    nodes = scan_directory(path=path, query=query)
    if not nodes:
        raise ValueError(f"No files found in {path}")
    files = extract_files_content(query=query, node=nodes, max_file_size=query["max_file_size"])
    summary = create_summary_string(query, nodes)
    tree = "Directory structure:\n" + create_tree_structure(query, nodes)
    files_content = create_file_content_string(files)

    formatted_tokens = generate_token_string(tree + files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def ingest_from_query(query: dict[str, Any]) -> tuple[str, str, str]:
    """Main entry point for analyzing a codebase directory or single file."""
    path = f"{query['local_path']}{query['subpath']}"
    if not os.path.exists(path):
        raise ValueError(f"{query['slug']} cannot be found")

    if query.get("type") == "blob":
        return ingest_single_file(path, query)

    return ingest_directory(path, query)
