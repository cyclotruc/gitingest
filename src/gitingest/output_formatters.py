""" Functions to ingest and analyze a codebase directory or single file. """

from typing import Optional, Tuple

import tiktoken

from gitingest.filesystem_schema import FileSystemNode, FileSystemNodeType
from gitingest.query_parsing import ParsedQuery


def _create_summary_string(query: ParsedQuery, node: FileSystemNode) -> str:
    """
    Create a summary string with file counts and content size.

    This function generates a summary of the repository's contents, including the number
    of files analyzed, the total content size, and other relevant details based on the query parameters.

    Parameters
    ----------
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    node : FileSystemNode
        The root node representing the directory structure, including file and directory counts.

    Returns
    -------
    str
        Summary string containing details such as repository name, file count, and other query-specific information.
    """
    if query.user_name:
        summary = f"Repository: {query.user_name}/{query.repo_name}\n"
    else:
        # Local scenario
        summary = f"Directory: {query.slug}\n"

    if query.commit:
        summary += f"Commit: {query.commit}\n"
    elif query.branch and query.branch not in ("main", "master"):
        summary += f"Branch: {query.branch}\n"

    if query.subpath != "/":
        summary += f"Subpath: {query.subpath}\n"

    summary += f"Files analyzed: {node.file_count}\n"
    # TODO: Do we want to add the total number of lines?

    return summary


def format_single_file(file_node: FileSystemNode, query: ParsedQuery) -> Tuple[str, str, str]:
    """
    Format a single file for display.

    This function generates a summary, tree structure, and content for a single file.
    It includes information such as the repository name, commit/branch, file name,
    line count, and estimated token count.

    Parameters
    ----------
    file_node : FileSystemNode
        The node representing the file to format.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    Tuple[str, str, str]
        A tuple containing the summary, tree structure, and file content.

    Raises
    ------
    ValueError
        If the file has no content.
    """
    if not file_node.content:
        raise ValueError(f"File {file_node.name} has no content")

    summary = f"Repository: {query.user_name}/{query.repo_name}\n"

    if query.commit:
        summary += f"Commit: {query.commit}\n"
    elif query.branch and query.branch not in ("main", "master"):
        summary += f"Branch: {query.branch}\n"

    summary += f"File: {file_node.name}\n"
    summary += f"Lines: {len(file_node.content.splitlines()):,}\n"

    files_content = file_node.content_string

    tree = "Directory structure:\n└── " + file_node.name

    formatted_tokens = _generate_token_string(files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content


def _get_files_content(node: FileSystemNode) -> str:
    if node.type == FileSystemNodeType.FILE:
        return node.content_string
    if node.type == FileSystemNodeType.DIRECTORY:
        return "\n".join(_get_files_content(child) for child in node.children)
    return ""


def _create_tree_structure(query: ParsedQuery, node: FileSystemNode, prefix: str = "", is_last: bool = True) -> str:
    """
    Create a tree-like string representation of the file structure.

    This function generates a string representation of the directory structure, formatted
    as a tree with appropriate indentation for nested directories and files.

    Parameters
    ----------
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.
    node : FileSystemNode
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

    if not node.name:
        node.name = query.slug

    if node.name:
        current_prefix = "└── " if is_last else "├── "
        name = node.name + "/" if node.type == FileSystemNodeType.DIRECTORY else node.name
        tree += prefix + current_prefix + name + "\n"

    if node.type == FileSystemNodeType.DIRECTORY:
        # Adjust prefix only if we added a node name
        new_prefix = prefix + ("    " if is_last else "│   ") if node.name else prefix
        children = node.children
        for i, child in enumerate(children):
            tree += _create_tree_structure(query, node=child, prefix=new_prefix, is_last=i == len(children) - 1)

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
    except (ValueError, UnicodeEncodeError) as exc:
        print(exc)
        return None

    if total_tokens > 1_000_000:
        return f"{total_tokens / 1_000_000:.1f}M"

    if total_tokens > 1_000:
        return f"{total_tokens / 1_000:.1f}k"

    return str(total_tokens)


def format_directory(root_node: FileSystemNode, query: ParsedQuery) -> Tuple[str, str, str]:
    """
    Ingest an entire directory and return its summary, directory structure, and file contents.

    This function processes a directory, extracts its contents, and generates a summary,
    directory structure, and file content. It recursively processes subdirectories as well.

    Parameters
    ----------
    root_node : FileSystemNode
        The root node representing the directory to process.
    query : ParsedQuery
        The parsed query object containing information about the repository and query parameters.

    Returns
    -------
    Tuple[str, str, str]
        A tuple containing the summary, directory structure, and file contents.
    """
    summary = _create_summary_string(query, node=root_node)
    tree = "Directory structure:\n" + _create_tree_structure(query, root_node)
    files_content = _get_files_content(root_node)

    formatted_tokens = _generate_token_string(tree + files_content)
    if formatted_tokens:
        summary += f"\nEstimated tokens: {formatted_tokens}"

    return summary, tree, files_content
