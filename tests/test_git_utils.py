"""
Tests for the `git_utils` module.

These tests validate the `validate_github_token` function, which ensures that
GitHub personal access tokens (PATs) are properly formatted.
"""

import base64

import pytest

from gitingest.utils.exceptions import InvalidGitHubTokenError
from gitingest.utils.git_utils import (
    create_git_auth_header,
    create_git_command,
    validate_github_token,
)


@pytest.mark.parametrize(
    "token",
    [
        # Valid tokens: correct prefixes and at least 36 allowed characters afterwards
        "github_pat_" + "a" * 36,
        "ghp_" + "A" * 36,
        "github_pat_1234567890abcdef1234567890abcdef1234",
    ],
)
def test_validate_github_token_valid(token):
    """validate_github_token should accept properly-formatted tokens."""
    # Should not raise any exception
    validate_github_token(token)


@pytest.mark.parametrize(
    "token",
    [
        "github_pat_short",  # Too short after prefix
        "ghp_" + "b" * 35,  # one character short
        "invalidprefix_" + "c" * 36,  # Wrong prefix
        "github_pat_" + "!" * 36,  # Disallowed characters
        "",  # Empty string
    ],
)
def test_validate_github_token_invalid(token):
    """validate_github_token should raise ValueError on malformed tokens."""
    with pytest.raises(InvalidGitHubTokenError):
        validate_github_token(token)


@pytest.mark.parametrize(
    "base_cmd, local_path, url, token, expected_suffix",
    [
        (
            ["git", "clone"],
            "/some/path",
            "https://github.com/owner/repo.git",
            None,
            [],  # No auth header expected when token is None
        ),
        (
            ["git", "clone"],
            "/some/path",
            "https://github.com/owner/repo.git",
            "ghp_" + "d" * 36,
            [
                "-c",
                create_git_auth_header("ghp_" + "d" * 36),
            ],  # Auth header expected for GitHub URL + token
        ),
        (
            ["git", "clone"],
            "/some/path",
            "https://gitlab.com/owner/repo.git",
            "ghp_" + "e" * 36,
            [],  # No auth header for non-GitHub URL even if token provided
        ),
    ],
)
def test_create_git_command(base_cmd, local_path, url, token, expected_suffix):
    """create_git_command should build the correct command list based on inputs."""
    cmd = create_git_command(base_cmd, local_path, url, token)

    # The command should start with base_cmd and the -C option
    expected_prefix = base_cmd + ["-C", local_path]
    assert cmd[: len(expected_prefix)] == expected_prefix

    # The suffix (anything after prefix) should match expected
    assert cmd[len(expected_prefix) :] == expected_suffix


def test_create_git_command_invalid_token():
    """Supplying an invalid token for a GitHub URL should raise ValueError."""
    with pytest.raises(InvalidGitHubTokenError):
        create_git_command(
            ["git", "clone"],
            "/some/path",
            "https://github.com/owner/repo.git",
            "invalid_token",
        )


@pytest.mark.parametrize(
    "token",
    [
        "ghp_abcdefghijklmnopqrstuvwxyz012345",  # typical ghp_ token
        "github_pat_1234567890abcdef1234567890abcdef1234",
    ],
)
def test_create_git_auth_header(token):
    """create_git_auth_header should produce correct base64-encoded header."""
    header = create_git_auth_header(token)
    expected_basic = base64.b64encode(f"x-oauth-basic:{token}".encode()).decode()
    expected = f"http.https://github.com/.extraheader=Authorization: Basic {expected_basic}"
    assert header == expected


@pytest.mark.parametrize(
    "url, token, should_call",
    [
        ("https://github.com/foo/bar.git", "ghp_" + "f" * 36, True),
        ("https://github.com/foo/bar.git", None, False),
        ("https://gitlab.com/foo/bar.git", "ghp_" + "g" * 36, False),
    ],
)
def test_create_git_command_helper_calls(mocker, url, token, should_call):
    """Verify validate_github_token & create_git_auth_header are invoked only when appropriate."""

    validate_mock = mocker.patch("gitingest.utils.git_utils.validate_github_token")
    header_mock = mocker.patch("gitingest.utils.git_utils.create_git_auth_header", return_value="HEADER")

    cmd = create_git_command(["git", "clone"], "/tmp", url, token)

    if should_call:
        validate_mock.assert_called_once_with(token)
        header_mock.assert_called_once_with(token)
        assert "HEADER" in cmd
    else:
        validate_mock.assert_not_called()
        header_mock.assert_not_called()
        # HEADER should not be included in command list
        assert "HEADER" not in cmd
