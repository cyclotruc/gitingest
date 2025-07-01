"""Utilities for handling authentication."""

from __future__ import annotations

import os

from gitingest.utils.git_utils import validate_github_token


def resolve_token(token: str | None) -> str | None:
    """Resolve the token to use for the query.

    Parameters
    ----------
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    str | None
        The resolved token.

    """
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        validate_github_token(token)
    return token
