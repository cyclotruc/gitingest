""" This module contains functions to parse and validate input sources and patterns. """

import re
import uuid
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple, Union
from urllib.parse import unquote, urlparse

from gitingest.cloning import _check_repo_exists, fetch_remote_branch_list, fetch_remote_tag_list
from gitingest.config import MAX_FILE_SIZE, TMP_BASE_PATH
from gitingest.exceptions import InvalidPatternError
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


@dataclass
class ParsedQuery:  # pylint: disable=too-many-instance-attributes
    """
    Dataclass to store the parsed details of the repository or file path.
    """

    user_name: Optional[str]
    repo_name: Optional[str]
    subpath: str
    local_path: Path
    url: Optional[str]
    slug: str
    id: str
    type: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    commit: Optional[str] = None
    max_file_size: int = MAX_FILE_SIZE
    ignore_patterns: Optional[Set[str]] = None
    include_patterns: Optional[Set[str]] = None
    pattern_type: Optional[str] = None
    include_submodules: bool = False


async def parse_query(
    source: str,
    max_file_size: int,
    from_web: bool,
    include_patterns: Optional[Union[str, Set[str]]] = None,
    ignore_patterns: Optional[Union[str, Set[str]]] = None,
    include_submodules: bool = False,
) -> ParsedQuery:
    """
    Parse the input source (URL or path) to extract relevant details for the query.

    This function parses the input source to extract details such as the username, repository name,
    commit hash, branch name, tag name, and other relevant information. It also processes the include and ignore
    patterns to filter the files and directories to include or exclude from the query.

    Parameters
    ----------
    source : str
        The source URL or file path to parse.
    max_file_size : int
        The maximum file size in bytes to include.
    from_web : bool
        Flag indicating whether the source is a web URL.
    include_patterns : Union[str, Set[str]], optional
        Patterns to include, by default None. Can be a set of strings or a single string.
    ignore_patterns : Union[str, Set[str]], optional
        Patterns to ignore, by default None. Can be a set of strings or a single string.
    include_submodules : bool
        Whether to include git submodules in the analysis

    Returns
    -------
    ParsedQuery
        A dataclass object containing the parsed details of the repository or file path.
    """

    # Determine the parsing method based on the source type
    if from_web or urlparse(source).scheme in ("https", "http") or any(h in source for h in KNOWN_GIT_HOSTS):
        # We either have a full URL or a domain-less slug
        parsed_query = await _parse_remote_repo(source)
    else:
        # Local path scenario
        parsed_query = _parse_local_dir_path(source)

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

    return ParsedQuery(
        user_name=parsed_query.user_name,
        repo_name=parsed_query.repo_name,
        url=parsed_query.url,
        subpath=parsed_query.subpath,
        local_path=parsed_query.local_path,
        slug=parsed_query.slug,
        id=parsed_query.id,
        type=parsed_query.type,
        branch=parsed_query.branch,
        tag=parsed_query.tag,
        commit=parsed_query.commit,
        max_file_size=max_file_size,
        ignore_patterns=ignore_patterns_set,
        include_patterns=parsed_include,
        include_submodules=include_submodules,
    )


async def _parse_remote_repo(source: str) -> ParsedQuery:
    """
    Parse a repository URL into a structured query dictionary.

    If source is:
      - A fully qualified URL (https://gitlab.com/...), parse & verify that domain
      - A URL missing 'https://' (gitlab.com/...), add 'https://' and parse
      - A 'slug' (like 'pandas-dev/pandas'), attempt known domains until we find one that exists.

    Parameters
    ----------
    source : str
        The URL or domain-less slug to parse.

    Returns
    -------
    ParsedQuery
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
            host = await try_domains_for_user_and_repo(*_get_user_and_repo_from_path(source))
            source = f"{host}/{source}"

        source = "https://" + source
        parsed_url = urlparse(source)

    host = parsed_url.netloc.lower()
    user_name, repo_name = _get_user_and_repo_from_path(parsed_url.path)

    _id = str(uuid.uuid4())
    slug = f"{user_name}-{repo_name}"
    local_path = TMP_BASE_PATH / _id / slug
    url = f"https://{host}/{user_name}/{repo_name}"

    parsed = ParsedQuery(
        user_name=user_name,
        repo_name=repo_name,
        url=url,
        subpath="/",
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

    # Git reference (commit, branch, or tag)
    git_reference = remaining_parts[0]
    if _is_valid_git_commit_hash(git_reference):
        parsed.commit = git_reference
        remaining_parts.pop(0)
    else:
        # Try to configure branch first
        parsed.branch, remaining_parts = await _configure_branch_and_subpath(remaining_parts, url)
        if parsed.branch is None:
            # If no branch is matched, try to configure tag
            parsed.tag, remaining_parts = await _configure_tag_and_subpath(remaining_parts, url)

    # Subpath if anything left
    if remaining_parts:
        parsed.subpath += "/".join(remaining_parts)

    return parsed


async def _configure_branch_and_subpath(remaining_parts: List[str], url: str) -> Tuple[Optional[str], List[str]]:
    """
    Configure the branch and subpath based on the remaining parts of the URL.
    Parameters
    ----------
    remaining_parts : List[str]
        The remaining parts of the URL path.
    url : str
        The URL of the repository.
    Returns
    -------
    Tuple[str, List[str]]
        - The branch name if found, otherwise None.
        - The remaining parts of the URL path.
    """
    try:
        # Fetch the list of branches from the remote repository
        branches: List[str] = await fetch_remote_branch_list(url)
    except RuntimeError as exc:
        warnings.warn(f"Warning: Failed to fetch branch list: {exc}", RuntimeWarning)
        return remaining_parts.pop(0), remaining_parts

    branch = []
    for part in remaining_parts:
        branch.append(part)
        branch_name = "/".join(branch)
        if branch_name in branches:
            # Only remove the branch name from the remaining parts if it matches a remote branch
            remaining_parts = remaining_parts[len(branch) :]
            return branch_name, remaining_parts

    return None, remaining_parts


async def _configure_tag_and_subpath(remaining_parts: List[str], url: str) -> Tuple[Optional[str], List[str]]:
    """
    Configure the tag and subpath based on the remaining parts of the URL.
    Parameters
    ----------
    remaining_parts : List[str]
        The remaining parts of the URL path.
    url : str
        The URL of the repository.
    Returns
    -------
    Tuple[str, List[str]]
        - The tag name if found, otherwise None.
        - The remaining parts of the URL path.
    """
    try:
        # Fetch the list of tags from the remote repository
        tags: List[str] = await fetch_remote_tag_list(url)
    except RuntimeError as exc:
        warnings.warn(f"Warning: Failed to fetch tag list: {exc}", RuntimeWarning)
        return remaining_parts.pop(0), remaining_parts

    tag = []
    for part in remaining_parts:
        tag.append(part)
        tag_name = "/".join(tag)
        if tag_name in tags:
            # Only remove the tag name from the remaining parts if it matches a remote tag
            remaining_parts = remaining_parts[len(tag) :]
            return tag_name, remaining_parts

    return None, remaining_parts


def _parse_patterns(pattern: Union[str, Set[str]]) -> Set[str]:
    """
    Parse and validate file/directory patterns for inclusion or exclusion.

    Takes either a single pattern string or set of pattern strings and processes them into a normalized list.
    Patterns are split on commas and spaces, validated for allowed characters, and normalized.

    Parameters
    ----------
    pattern : Set[str] | str
        Pattern(s) to parse - either a single string or set of strings

    Returns
    -------
    Set[str]
        A set of normalized patterns.

    Raises
    ------
    InvalidPatternError
        If any pattern contains invalid characters. Only alphanumeric characters,
        dash (-), underscore (_), dot (.), forward slash (/), plus (+), and
        asterisk (*) are allowed.
    """
    patterns = pattern if isinstance(pattern, set) else {pattern}

    parsed_patterns: Set[str] = set()
    for p in patterns:
        parsed_patterns = parsed_patterns.union(set(re.split(",| ", p)))

    # Remove empty string if present
    parsed_patterns = parsed_patterns - {""}

    # Validate and normalize each pattern
    for p in parsed_patterns:
        if not _is_valid_pattern(p):
            raise InvalidPatternError(p)

    return {_normalize_pattern(p) for p in parsed_patterns}


def _parse_local_dir_path(path_str: str) -> ParsedQuery:
    """
    Parse the given file path into a structured query dictionary.

    Parameters
    ----------
    path_str : str
        The file path to parse.

    Returns
    -------
    ParsedQuery
        A dictionary containing the parsed details of the file path.
    """
    path_obj = Path(path_str).resolve()
    slug = path_obj.name if path_str == "." else path_str.strip("/")
    return ParsedQuery(
        user_name=None,
        repo_name=None,
        url=None,
        subpath="/",
        local_path=path_obj,
        slug=slug,
        id=str(uuid.uuid4()),
    )


async def try_domains_for_user_and_repo(user_name: str, repo_name: str) -> str:
    """
    Attempt to find a valid repository host for the given user_name and repo_name.

    Parameters
    ----------
    user_name : str
        The username or owner of the repository.
    repo_name : str
        The name of the repository.

    Returns
    -------
    str
        The domain of the valid repository host.

    Raises
    ------
    ValueError
        If no valid repository host is found for the given user_name and repo_name.
    """
    for domain in KNOWN_GIT_HOSTS:
        candidate = f"https://{domain}/{user_name}/{repo_name}"
        if await _check_repo_exists(candidate):
            return domain
    raise ValueError(f"Could not find a valid repository host for '{user_name}/{repo_name}'.")


def simplify_condition(condition: Any) -> Any:
    """
    Simplify a condition by reducing it to its simplest form.

    Parameters
    ----------
    condition : Any
        The condition to simplify

    Returns
    -------
    Any
        The simplified condition
    """
    result = bool(condition)
    return result
