import os
import string
import uuid
from typing import Any
from urllib.parse import unquote

from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS

TMP_BASE_PATH: str = "../tmp"
HEX_DIGITS = set(string.hexdigits)


def _parse_url(url: str) -> dict[str, Any]:
    url = url.split(" ")[0]
    url = unquote(url)  # Decode URL-encoded characters

    if not url.startswith("https://"):
        url = "https://" + url

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
        "local_path": f"{TMP_BASE_PATH}/{_id}/{slug}",
        "url": f"https://{domain}/{user_name}/{repo_name}",
        "slug": slug,
        "id": _id,
    }

    # If this is an issues page, return early without processing subpath
    if len(path_parts) > 2 and (path_parts[2] == "issues" or path_parts[2] == "pull"):
        return parsed

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
    return len(commit) == 40 and all(c in HEX_DIGITS for c in commit)


def _normalize_pattern(pattern: str) -> str:
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern


def _parse_patterns(pattern: list[str] | str) -> list[str]:
    patterns = pattern if isinstance(pattern, list) else [pattern]
    patterns = [p.strip() for p in patterns]

    for p in patterns:
        if not all(c.isalnum() or c in "-_./+*" for c in p):
            raise ValueError(
                f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), "
                "underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed."
            )

    return [_normalize_pattern(p) for p in patterns]


def _override_ignore_patterns(ignore_patterns: list[str], include_patterns: list[str]) -> list[str]:
    """
    Removes patterns from ignore_patterns that are present in include_patterns using set difference.

    Parameters
    ----------
    ignore_patterns : List[str]
        The list of patterns to potentially remove.
    include_patterns : List[str]
        The list of patterns to exclude from ignore_patterns.

    Returns
    -------
    List[str]
        A new list of ignore_patterns with specified patterns removed.
    """
    return list(set(ignore_patterns) - set(include_patterns))


def _parse_path(path: str) -> dict[str, Any]:
    query = {
        "url": None,
        "local_path": os.path.abspath(path),
        "slug": os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path),
        "subpath": "/",
        "id": str(uuid.uuid4()),
    }
    return query


def parse_query(
    source: str,
    max_file_size: int,
    from_web: bool,
    include_patterns: list[str] | str | None = None,
    ignore_patterns: list[str] | str | None = None,
) -> dict[str, Any]:
    """
    Parses the input source to construct a query dictionary with specified parameters.

    Parameters
    ----------
    source : str
        The source URL or file path to parse.
    max_file_size : int
        The maximum file size in bytes to include.
    from_web : bool
        Flag indicating whether the source is a web URL.
    include_patterns : Optional[Union[List[str], str]], optional
        Patterns to include, by default None. Can be a list of strings or a single string.
    ignore_patterns : Optional[Union[List[str], str]], optional
        Patterns to ignore, by default None. Can be a list of strings or a single string.

    Returns
    -------
    Dict[str, Any]
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
