"""Module containing functions to parse and validate input sources and patterns."""

from __future__ import annotations

import re
import uuid
import warnings
from pathlib import Path
from urllib.parse import unquote, urlparse

from gitingest.config import TMP_BASE_PATH
from gitingest.schemas import IngestionQuery
from gitingest.utils.exceptions import InvalidPatternError
from gitingest.utils.git_utils import check_repo_exists, fetch_remote_branch_list
from gitingest.utils.ignore_patterns import DEFAULT_IGNORE_PATTERNS
from gitingest.utils.query_parser_utils import (
    KNOWN_GIT_HOSTS,
    _get_user_and_repo_from_path,
    _is_valid_git_commit_hash,
    _is_valid_pattern,
    _normalize_pattern,
    _validate_host,
    _validate_url_scheme,
)


async def parse_query(
    source: str,
    *,
    max_file_size: int,
    from_web: bool,
    include_patterns: set[str] | str | None = None,
    ignore_patterns: set[str] | str | None = None,
    token: str | None = None,
) -> IngestionQuery:
    """Parse the input source to extract details for the query and process the include and ignore patterns.

    Parameters
    ----------
    source : str
        The source URL or file path to parse.
    max_file_size : int
        The maximum file size in bytes to include.
    from_web : bool
        Flag indicating whether the source is a web URL.
    include_patterns : set[str] | str | None
        Patterns to include. Can be a set of strings or a single string.
    ignore_patterns : set[str] | str | None
        Patterns to ignore. Can be a set of strings or a single string.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    IngestionQuery
        A dataclass object containing the parsed details of the repository or file path.

    """
    # Determine the parsing method based on the source type
    if from_web or urlparse(source).scheme in ("https", "http") or any(h in source for h in KNOWN_GIT_HOSTS):
        # We either have a full URL or a domain-less slug
        query = await _parse_remote_repo(source, token=token)
    else:
        # Local path scenario
        query = _parse_local_dir_path(source)

    # Combine default ignore patterns + custom patterns
    ignore_patterns_set = DEFAULT_IGNORE_PATTERNS.copy()
    if ignore_patterns:
        ignore_patterns_set.update(_parse_patterns(ignore_patterns))

    # Process include patterns and override ignore patterns accordingly
    if include_patterns:
        parsed_include = _parse_patterns(include_patterns)
        # Override ignore patterns with include patterns
        ignore_patterns_set = set(ignore_patterns_set) - set(parsed_include)
    else:
        parsed_include = None

    return IngestionQuery(
        user_name=query.user_name,
        repo_name=query.repo_name,
        url=query.url,
        subpath=query.subpath,
        local_path=query.local_path,
        slug=query.slug,
        id=query.id,
        type=query.type,
        branch=query.branch,
        commit=query.commit,
        max_file_size=max_file_size,
        ignore_patterns=ignore_patterns_set,
        include_patterns=parsed_include,
    )


async def _parse_remote_repo(source: str, token: str | None = None) -> IngestionQuery:
    """Parse a repository URL into a structured query dictionary.

    If source is:
      - A fully qualified URL ('https://gitlab.com/...'), parse & verify that domain
      - A URL missing 'https://' ('gitlab.com/...'), add 'https://' and parse
      - A *slug* ('pandas-dev/pandas'), attempt known domains until we find one that exists.

    Parameters
    ----------
    source : str
        The URL or domain-less slug to parse.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    IngestionQuery
        A dictionary containing the parsed details of the repository.

    """
    source = unquote(source)

    # Attempt to parse
    parsed_url = urlparse(source)

    if parsed_url.scheme:
        _validate_url_scheme(parsed_url.scheme)
        _validate_host(parsed_url.netloc.lower())

    else:  # Will be of the form 'host/user/repo' or 'user/repo'
        tmp_host = source.split("/")[0].lower()
        if "." in tmp_host:
            _validate_host(tmp_host)
        else:
            # No scheme, no domain => user typed "user/repo", so we'll guess the domain.
            host = await try_domains_for_user_and_repo(*_get_user_and_repo_from_path(source), token=token)
            source = f"{host}/{source}"

        source = "https://" + source
        parsed_url = urlparse(source)

    host = parsed_url.netloc.lower()
    user_name, repo_name = _get_user_and_repo_from_path(parsed_url.path)

    _id = str(uuid.uuid4())
    slug = f"{user_name}-{repo_name}"
    local_path = TMP_BASE_PATH / _id / slug
    url = f"https://{host}/{user_name}/{repo_name}"

    parsed = IngestionQuery(
        user_name=user_name,
        repo_name=repo_name,
        url=url,
        local_path=local_path,
        slug=slug,
        id=_id,
    )

    remaining_parts = parsed_url.path.strip("/").split("/")[2:]

    if not remaining_parts:
        return parsed

    possible_type = remaining_parts.pop(0)  # e.g. 'issues', 'pull', 'tree', 'blob'

    # If no extra path parts, just return
    if not remaining_parts:
        return parsed

    # If this is an issues page or pull requests, return early without processing subpath
    if remaining_parts and possible_type in ("issues", "pull"):
        return parsed

    parsed.type = possible_type

    # Commit or branch
    commit_or_branch = remaining_parts[0]
    if _is_valid_git_commit_hash(commit_or_branch):
        parsed.commit = commit_or_branch
        remaining_parts.pop(0)
    else:
        parsed.branch = await _configure_branch_and_subpath(remaining_parts, url)

    # Subpath if anything left
    if remaining_parts:
        parsed.subpath += "/".join(remaining_parts)

    return parsed


async def _configure_branch_and_subpath(remaining_parts: list[str], url: str) -> str | None:
    """Configure the branch and subpath based on the remaining parts of the URL.

    Parameters
    ----------
    remaining_parts : list[str]
        The remaining parts of the URL path.
    url : str
        The URL of the repository.

    Returns
    -------
    str | None
        The branch name if found, otherwise ``None``.

    """
    try:
        # Fetch the list of branches from the remote repository
        branches: list[str] = await fetch_remote_branch_list(url)
    except RuntimeError as exc:
        warnings.warn(f"Warning: Failed to fetch branch list: {exc}", RuntimeWarning, stacklevel=2)
        return remaining_parts.pop(0)

    branch = []
    while remaining_parts:
        branch.append(remaining_parts.pop(0))
        branch_name = "/".join(branch)
        if branch_name in branches:
            return branch_name

    return None


def _parse_patterns(pattern: set[str] | str) -> set[str]:
    """Parse and validate file/directory patterns for inclusion or exclusion.

    Takes either a single pattern string or set of pattern strings and processes them into a normalized list.
    Patterns are split on commas and spaces, validated for allowed characters, and normalized.

    Parameters
    ----------
    pattern : set[str] | str
        Pattern(s) to parse - either a single string or set of strings

    Returns
    -------
    set[str]
        A set of normalized patterns.

    Raises
    ------
    InvalidPatternError
        If any pattern contains invalid characters. Only alphanumeric characters,
        dash (-), underscore (_), dot (.), forward slash (/), plus (+), and
        asterisk (*) are allowed.

    """
    patterns = pattern if isinstance(pattern, set) else {pattern}

    parsed_patterns: set[str] = set()
    for p in patterns:
        parsed_patterns = parsed_patterns.union(set(re.split(",| ", p)))

    # Remove empty string if present
    parsed_patterns = parsed_patterns - {""}

    # Normalize Windows paths to Unix-style paths
    parsed_patterns = {p.replace("\\", "/") for p in parsed_patterns}

    # Validate and normalize each pattern
    for p in parsed_patterns:
        if not _is_valid_pattern(p):
            raise InvalidPatternError(p)

    return {_normalize_pattern(p) for p in parsed_patterns}


def _parse_local_dir_path(path_str: str) -> IngestionQuery:
    """Parse the given file path into a structured query dictionary.

    Parameters
    ----------
    path_str : str
        The file path to parse.

    Returns
    -------
    IngestionQuery
        A dictionary containing the parsed details of the file path.

    """
    path_obj = Path(path_str).resolve()
    slug = path_obj.name if path_str == "." else path_str.strip("/")
    return IngestionQuery(
        user_name=None,
        repo_name=None,
        url=None,
        local_path=path_obj,
        slug=slug,
        id=str(uuid.uuid4()),
    )


async def try_domains_for_user_and_repo(user_name: str, repo_name: str, token: str | None = None) -> str:
    """Attempt to find a valid repository host for the given ``user_name`` and ``repo_name``.

    Parameters
    ----------
    user_name : str
        The username or owner of the repository.
    repo_name : str
        The name of the repository.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    str
        The domain of the valid repository host.

    Raises
    ------
    ValueError
        If no valid repository host is found for the given ``user_name`` and ``repo_name``.

    """
    for domain in KNOWN_GIT_HOSTS:
        candidate = f"https://{domain}/{user_name}/{repo_name}"
        if await check_repo_exists(candidate, token=token if domain.startswith("github.") else None):
            return domain

    msg = f"Could not find a valid repository host for '{user_name}/{repo_name}'."
    raise ValueError(msg)
