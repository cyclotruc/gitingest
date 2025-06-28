"""Utilities for handling authentication."""

from __future__ import annotations

import os


def resolve_token(token: str | None) -> str | None:
    """Resolve the token to use for the query.

    Parameters
    ----------
    token : str | None
        The token to use for the query.

    Returns
    -------
    str | None
        The resolved token.

    """
    return token or os.getenv("GITHUB_TOKEN")
