""" Utility functions for parsing and validating query parameters. """

import os
import string
from typing import List, Set, Tuple

HEX_DIGITS: Set[str] = set(string.hexdigits)


KNOWN_GIT_HOSTS: List[str] = [
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "gitea.com",
    "codeberg.org",
    "gist.github.com",
]


def _is_valid_git_commit_hash(commit: str) -> bool:
    """
    Validate if the provided string is a valid Git commit hash.

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


def _is_valid_pattern(pattern: str) -> bool:
    """
    Validate if the given pattern contains only valid characters.

    This function checks if the pattern contains only alphanumeric characters or one
    of the following allowed characters: dash (`-`), underscore (`_`), dot (`.`),
    forward slash (`/`), plus (`+`), asterisk (`*`), or the at sign (`@`).

    Parameters
    ----------
    pattern : str
        The pattern to validate.

    Returns
    -------
    bool
        True if the pattern is valid, otherwise False.
    """
    return all(c.isalnum() or c in "-_./+*@" for c in pattern)


def _validate_host(host: str) -> None:
    """
    Validate the given host against the known Git hosts.

    Parameters
    ----------
    host : str
        The host to validate.

    Raises
    ------
    ValueError
        If the host is not a known Git host.
    """
    if host not in KNOWN_GIT_HOSTS:
        raise ValueError(f"Unknown domain '{host}' in URL")


def _validate_url_scheme(scheme: str) -> None:
    """
    Validate the given scheme against the known schemes.

    Parameters
    ----------
    scheme : str
        The scheme to validate.

    Raises
    ------
    ValueError
        If the scheme is not 'http' or 'https'.
    """
    if scheme not in ("https", "http"):
        raise ValueError(f"Invalid URL scheme '{scheme}' in URL")


def _get_user_and_repo_from_path(path: str) -> Tuple[str, str]:
    """
    Extract the user and repository names from a given path.

    Parameters
    ----------
    path : str
        The path to extract the user and repository names from.

    Returns
    -------
    Tuple[str, str]
        A tuple containing the user and repository names.

    Raises
    ------
    ValueError
        If the path does not contain at least two parts.
    """
    path_parts = path.lower().strip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"Invalid repository URL '{path}'")
    return path_parts[0], path_parts[1]


def _normalize_pattern(pattern: str) -> str:
    """
    Normalize the given pattern by removing leading separators and appending a wildcard.

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
