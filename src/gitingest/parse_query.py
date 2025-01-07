""" This module contains functions to parse and validate input sources and patterns. """

import os
import re
import string
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from config import TMP_BASE_PATH
from gitingest.exceptions import InvalidPatternError
from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS

HEX_DIGITS = set(string.hexdigits)


def parse_query(
    source: str,
    max_file_size: int,
    from_web: bool,
    include_patterns: list[str] | str | None = None,
    ignore_patterns: list[str] | str | None = None,
) -> dict[str, Any]:
    """
    Parse the input source to construct a query dictionary with specified parameters.

    This function processes the provided source (either a URL or file path) and builds a
    query dictionary that includes information such as the source URL, maximum file size,
    and any patterns to include or ignore. It handles both web and file-based sources.

    Parameters
    ----------
    source : str
        The source URL or file path to parse.
    max_file_size : int
        The maximum file size in bytes to include.
    from_web : bool
        Flag indicating whether the source is a web URL.
    include_patterns : list[str] | str | None, optional
        Patterns to include, by default None. Can be a list of strings or a single string.
    ignore_patterns : list[str] | str | None, optional
        Patterns to ignore, by default None. Can be a list of strings or a single string.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the parsed query parameters, including 'max_file_size',
        'ignore_patterns', and 'include_patterns'.
    """
    # Determine the parsing method based on the source type
    if from_web or source.startswith("https://") or "github.com" in source:
        query = _parse_url(source)
    else:
        query = _parse_path(source)

    # Process ignore patterns
    ignore_patterns_list = DEFAULT_IGNORE_PATTERNS.copy()
    if ignore_patterns:
        ignore_patterns_list += _parse_patterns(ignore_patterns)

    # Process include patterns and override ignore patterns accordingly
    if include_patterns:
        parsed_include = _parse_patterns(include_patterns)
        ignore_patterns_list = _override_ignore_patterns(ignore_patterns_list, include_patterns=parsed_include)
    else:
        parsed_include = None

    # Update the query dictionary with max_file_size and processed patterns
    query.update(
        {
            "max_file_size": max_file_size,
            "ignore_patterns": ignore_patterns_list,
            "include_patterns": parsed_include,
        }
    )
    return query


def _parse_url(url: str) -> dict[str, Any]:
    """
    Parse a GitHub repository URL into a structured query dictionary.

    This function extracts relevant information from a GitHub URL, such as the username,
    repository name, commit, branch, and subpath, and returns them in a structured format.

    Parameters
    ----------
    url : str
        The GitHub URL to parse.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the parsed details of the GitHub repository, including
        the username, repository name, commit, branch, and other relevant information.

    Raises
    ------
    ValueError
        If the URL is invalid or does not correspond to a valid Git repository.
    """
    # Clean up the URL
    url = url.split(" ")[0]  # remove trailing text
    url = unquote(url)  # decode URL-encoded characters

    if not url.startswith(("https://", "http://")):
        url = "https://" + url

    # Parse URL and reconstruct it without query parameters and fragments
    parsed_url = urlparse(url)
    url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    # Extract domain and path
    url_parts = url.split("/")
    domain = url_parts[2]
    path_parts = url_parts[3:]

    if len(path_parts) < 2:
        raise ValueError("Invalid repository URL. Please provide a valid Git repository URL.")

    user_name = path_parts[0]
    repo_name = path_parts[1]
    _id = str(uuid.uuid4())
    slug = f"{user_name}-{repo_name}"

    parsed = {
        "user_name": user_name,
        "repo_name": repo_name,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": Path(TMP_BASE_PATH) / _id / slug,
        "url": f"https://{domain}/{user_name}/{repo_name}",
        "slug": slug,
        "id": _id,
    }

    # If this is an issues page or pull requests, return early without processing subpath
    if len(path_parts) > 2 and (path_parts[2] == "issues" or path_parts[2] == "pull"):
        return parsed

    # If no extra path parts, just return
    if len(path_parts) < 4:
        return parsed

    parsed["type"] = path_parts[2]  # Usually 'tree' or 'blob'
    commit = path_parts[3]

    if _is_valid_git_commit_hash(commit):
        parsed["commit"] = commit
        if len(path_parts) > 4:
            parsed["subpath"] += "/".join(path_parts[4:])
    else:
        parsed["branch"] = commit
        if len(path_parts) > 4:
            parsed["subpath"] += "/".join(path_parts[4:])

    return parsed


def _is_valid_git_commit_hash(commit: str) -> bool:
    """
    Validates if the provided string is a valid Git commit hash.

    This function checks if the commit hash is a 40-character string consisting only
    of hexadecimal digits, which is the standard format for Git commit hashes.

    Parameters
    ----------
    commit : str
        The string to validate as a Git commit hash.

    Returns
    -------
    bool
        True if the string is a valid 40-character Git commit hash, otherwise False.
    """
    return len(commit) == 40 and all(c in HEX_DIGITS for c in commit)


def _normalize_pattern(pattern: str) -> str:
    """
    Normalizes the given pattern by removing leading separators and appending a wildcard.

    This function processes the pattern string by stripping leading directory separators
    and appending a wildcard (`*`) if the pattern ends with a separator.

    Parameters
    ----------
    pattern : str
        The pattern to normalize.

    Returns
    -------
    str
        The normalized pattern.
    """
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern


def _parse_patterns(pattern: list[str] | str) -> list[str]:
    """
    Parse and validate file/directory patterns for inclusion or exclusion.

    Takes either a single pattern string or list of pattern strings and processes them into a normalized list.
    Patterns are split on commas and spaces, validated for allowed characters, and normalized.

    Parameters
    ----------
    pattern : list[str] | str
        Pattern(s) to parse - either a single string or list of strings

    Returns
    -------
    list[str]
        List of normalized pattern strings

    Raises
    ------
    InvalidPatternError
        If any pattern contains invalid characters. Only alphanumeric characters,
        dash (-), underscore (_), dot (.), forward slash (/), plus (+), and
        asterisk (*) are allowed.
    """
    patterns = pattern if isinstance(pattern, list) else [pattern]

    parsed_patterns = []
    for p in patterns:
        parsed_patterns.extend(re.split(",| ", p))

    # Filter out any empty strings
    parsed_patterns = [p for p in parsed_patterns if p != ""]

    # Validate and normalize each pattern
    for p in parsed_patterns:
        if not _is_valid_pattern(p):
            raise InvalidPatternError(p)

    return [_normalize_pattern(p) for p in parsed_patterns]


def _override_ignore_patterns(ignore_patterns: list[str], include_patterns: list[str]) -> list[str]:
    """
    Removes patterns from ignore_patterns that are present in include_patterns using set difference.

    Parameters
    ----------
    ignore_patterns : list[str]
        The list of patterns to potentially remove.
    include_patterns : list[str]
        The list of patterns to exclude from ignore_patterns.

    Returns
    -------
    list[str]
        A new list of ignore_patterns with specified patterns removed.
    """
    return list(set(ignore_patterns) - set(include_patterns))


def _parse_path(path_str: str) -> dict[str, Any]:
    """
    Parses a file path into a structured query dictionary.

    This function takes a file path and constructs a query dictionary that includes
    relevant details such as the absolute path and the slug (a combination of the
    directory and file names).

    Parameters
    ----------
    path_str : str
        The file path to parse.

    Returns
    -------
    dict[str, Any]
        A dictionary containing parsed details such as the local file path and slug.
    """
    path_obj = Path(path_str).resolve()
    query = {
        "url": None,
        "local_path": path_obj,
        "slug": f"{path_obj.parent.name}/{path_obj.name}",
        "subpath": "/",
        "id": str(uuid.uuid4()),
    }
    return query


def _is_valid_pattern(pattern: str) -> bool:
    """
    Validates if the given pattern contains only valid characters.

    This function checks if the pattern contains only alphanumeric characters or one
    of the following allowed characters: dash (`-`), underscore (`_`), dot (`.`),
    forward slash (`/`), plus (`+`), or asterisk (`*`).

    Parameters
    ----------
    pattern : str
        The pattern to validate.

    Returns
    -------
    bool
        True if the pattern is valid, otherwise False.
    """
    return all(c.isalnum() or c in "-_./+*" for c in pattern)
