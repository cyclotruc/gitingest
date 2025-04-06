"""
Tests for the `cloning` module.

These tests cover various scenarios for cloning repositories, verifying that the appropriate Git commands are invoked
and handling edge cases such as nonexistent URLs, timeouts, redirects, and specific commits or branches.
"""

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from gitingest.cloning import check_repo_exists, clone_repo
from gitingest.schemas import CloneConfig
from gitingest.utils.exceptions import AsyncTimeoutError


@pytest.mark.asyncio
async def test_clone_with_commit(mocker) -> None:
    """
    Test cloning a repository with a specific commit hash.

    Given a valid URL and a commit hash:
    When `clone_repo` is called,
    Then the repository should be cloned and checked out at that commit.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit="a" * 40,  # Simulating a valid commit hash
        branch="main",
    )

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"output", b"error")
    mock_exec.return_value = mock_process

    await clone_repo(clone_config)

    mock_check.assert_called_once_with(clone_config.url)
    assert mock_exec.call_count == 2  # Clone and checkout calls


@pytest.mark.asyncio
async def test_clone_without_commit(mocker) -> None:
    """
    Test cloning a repository when no commit hash is provided.

    Given a valid URL and no commit hash:
    When `clone_repo` is called,
    Then only the clone_repo operation should be performed (no checkout).
    """
    query = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit=None,
        branch="main",
    )

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"output", b"error")
    mock_exec.return_value = mock_process

    await clone_repo(query)

    mock_check.assert_called_once_with(query.url)
    assert mock_exec.call_count == 1  # Only clone call


@pytest.mark.asyncio
async def test_clone_nonexistent_repository(mocker) -> None:
    """
    Test cloning a nonexistent repository URL.

    Given an invalid or nonexistent URL:
    When `clone_repo` is called,
    Then a ValueError should be raised with an appropriate error message.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/nonexistent-repo",
        local_path="/tmp/repo",
        commit=None,
        branch="main",
    )
    mock_check = mocker.patch("gitingest.cloning.check_repo_exists", return_value=False)
    with pytest.raises(ValueError, match="Repository not found or inaccessible"):
        await clone_repo(clone_config)

        mock_check.assert_called_once_with(clone_config.url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_stdout, return_code, expected",
    [
        (b"HTTP/1.1 200 OK\n", 0, True),  # Existing repo
        (b"HTTP/1.1 404 Not Found\n", 0, False),  # Non-existing repo
        (b"HTTP/1.1 200 OK\n", 1, False),  # Failed request
    ],
)
async def test_check_repo_exists(mock_stdout: bytes, return_code: int, expected: bool) -> None:
    """
    Test the `_check_repo_exists` function with different Git HTTP responses.

    Given various stdout lines and return codes:
    When `_check_repo_exists` is called,
    Then it should correctly indicate whether the repository exists.
    """
    url = "https://github.com/user/repo"

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        # Mock the subprocess output
        mock_process.communicate.return_value = (mock_stdout, b"")
        mock_process.returncode = return_code
        mock_exec.return_value = mock_process

        repo_exists = await check_repo_exists(url)

        assert repo_exists is expected


@pytest.mark.asyncio
async def test_clone_with_custom_branch(mocker) -> None:
    """
    Test cloning a repository with a specified custom branch.

    Given a valid URL and a branch:
    When `clone_repo` is called,
    Then the repository should be cloned shallowly to that branch.
    """
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo", branch="feature-branch")
    mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)
    await clone_repo(clone_config)

    mock_exec.assert_called_once_with(
        "git",
        "clone",
        "--single-branch",
        "--depth=1",
        "--branch",
        "feature-branch",
        clone_config.url,
        clone_config.local_path,
    )


@pytest.mark.asyncio
async def test_git_command_failure(mocker) -> None:
    """
    Test cloning when the Git command fails during execution.

    Given a valid URL, but `run_command` raises a RuntimeError:
    When `clone_repo` is called,
    Then a RuntimeError should be raised with the correct message.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
    )
    mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mocker.patch("gitingest.cloning.run_command", side_effect=RuntimeError("Git command failed"))
    with pytest.raises(RuntimeError, match="Git command failed"):
        await clone_repo(clone_config)


@pytest.mark.asyncio
async def test_clone_default_shallow_clone(mocker) -> None:
    """
    Test cloning a repository with the default shallow clone options.

    Given a valid URL and no branch or commit:
    When `clone_repo` is called,
    Then the repository should be cloned with `--depth=1` and `--single-branch`.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
    )

    mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)
    await clone_repo(clone_config)

    mock_exec.assert_called_once_with(
        "git",
        "clone",
        "--single-branch",
        "--depth=1",
        clone_config.url,
        clone_config.local_path,
    )


@pytest.mark.asyncio
async def test_clone_commit_without_branch(mocker) -> None:
    """
    Test cloning when a commit hash is provided but no branch is specified.

    Given a valid URL and a commit hash (but no branch):
    When `clone_repo` is called,
    Then the repository should be cloned and checked out at that commit.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit="a" * 40,  # Simulating a valid commit hash
    )
    mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)
    await clone_repo(clone_config)

    assert mock_exec.call_count == 2  # Clone and checkout calls
    mock_exec.assert_any_call("git", "clone", "--single-branch", clone_config.url, clone_config.local_path)
    mock_exec.assert_any_call("git", "-C", clone_config.local_path, "checkout", clone_config.commit)


@pytest.mark.asyncio
async def test_check_repo_exists_with_redirect() -> None:
    """
    Test `check_repo_exists` when a redirect (302) is returned.

    Given a URL that responds with "302 Found":
    When `check_repo_exists` is called,
    Then it should return `False`, indicating the repo is inaccessible.
    """
    url = "https://github.com/user/repo"
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 302 Found\n", b"")
        mock_process.returncode = 0  # Simulate successful request
        mock_exec.return_value = mock_process

        repo_exists = await check_repo_exists(url)

        assert repo_exists is False


@pytest.mark.asyncio
async def test_check_repo_exists_with_permanent_redirect() -> None:
    """
    Test `check_repo_exists` when a permanent redirect (301) is returned.

    Given a URL that responds with "301 Found":
    When `check_repo_exists` is called,
    Then it should return `True`, indicating the repo may exist at the new location.
    """
    url = "https://github.com/user/repo"
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 301 Found\n", b"")
        mock_process.returncode = 0  # Simulate successful request
        mock_exec.return_value = mock_process

        repo_exists = await check_repo_exists(url)

        assert repo_exists


@pytest.mark.asyncio
async def test_clone_with_timeout() -> None:
    """
    Test cloning a repository when a timeout occurs.

    Given a valid URL, but `run_command` times out:
    When `clone_repo` is called,
    Then an `AsyncTimeoutError` should be raised to indicate the operation exceeded time limits.
    """
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo")

    with patch("gitingest.cloning.check_repo_exists", return_value=True):
        with patch("gitingest.cloning.run_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = asyncio.TimeoutError
            with pytest.raises(AsyncTimeoutError, match="Operation timed out after"):
                await clone_repo(clone_config)


@pytest.mark.asyncio
async def test_clone_specific_branch(tmp_path):
    """
    Test cloning a specific branch of a repository.

    Given a valid repository URL and a branch name:
    When `clone_repo` is called,
    Then the repository should be cloned and checked out at that branch.
    """
    repo_url = "https://github.com/cyclotruc/gitingest.git"
    branch_name = "main"
    local_path = tmp_path / "gitingest"

    config = CloneConfig(url=repo_url, local_path=str(local_path), branch=branch_name)
    await clone_repo(config)

    # Assertions
    assert local_path.exists(), "The repository was not cloned successfully."
    assert local_path.is_dir(), "The cloned repository path is not a directory."

    # Check the current branch
    current_branch = os.popen(f"git -C {local_path} branch --show-current").read().strip()
    assert current_branch == branch_name, f"Expected branch '{branch_name}', got '{current_branch}'."


@pytest.mark.asyncio
async def test_clone_branch_with_slashes(tmp_path):
    """
    Test cloning a branch with slashes in the name.

    Given a valid repository URL and a branch name with slashes:
    When `clone_repo` is called,
    Then the repository should be cloned and checked out at that branch.
    """
    repo_url = "https://github.com/user/repo"
    branch_name = "fix/in-operator"
    local_path = tmp_path / "gitingest"

    clone_config = CloneConfig(url=repo_url, local_path=str(local_path), branch=branch_name)
    with patch("gitingest.cloning.check_repo_exists", return_value=True):
        with patch("gitingest.cloning.run_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            mock_exec.assert_called_once_with(
                "git",
                "clone",
                "--single-branch",
                "--depth=1",
                "--branch",
                "fix/in-operator",
                clone_config.url,
                clone_config.local_path,
            )


@pytest.mark.asyncio
async def test_clone_creates_parent_directory(tmp_path: Path) -> None:
    """
    Test that clone_repo creates parent directories if they don't exist.

    Given a local path with non-existent parent directories:
    When `clone_repo` is called,
    Then it should create the parent directories before attempting to clone.
    """
    nested_path = tmp_path / "deep" / "nested" / "path" / "repo"
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path=str(nested_path),
    )

    with patch("gitingest.cloning.check_repo_exists", return_value=True):
        with patch("gitingest.cloning.run_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            # Verify parent directory was created
            assert nested_path.parent.exists()

            # Verify git clone was called with correct parameters
            mock_exec.assert_called_once_with(
                "git",
                "clone",
                "--single-branch",
                "--depth=1",
                clone_config.url,
                str(nested_path),
            )


@pytest.mark.asyncio
async def test_clone_with_specific_subpath() -> None:
    """
    Test cloning a repository with a specific subpath.

    Given a valid repository URL and a specific subpath:
    When `clone_repo` is called,
    Then the repository should be cloned with sparse checkout enabled and the specified subpath.
    """
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo", subpath="src/docs")

    with patch("gitingest.cloning.check_repo_exists", return_value=True):
        with patch("gitingest.cloning.run_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            # Verify the clone command includes sparse checkout flags
            mock_exec.assert_any_call(
                "git",
                "clone",
                "--single-branch",
                "--filter=blob:none",
                "--sparse",
                "--depth=1",
                clone_config.url,
                clone_config.local_path,
            )

            # Verify the sparse-checkout command sets the correct path
            mock_exec.assert_any_call("git", "-C", clone_config.local_path, "sparse-checkout", "set", "src/docs")

            assert mock_exec.call_count == 2


@pytest.mark.asyncio
async def test_clone_with_commit_and_subpath() -> None:
    """
    Test cloning a repository with both a specific commit and subpath.

    Given a valid repository URL, commit hash, and subpath:
    When `clone_repo` is called,
    Then the repository should be cloned with sparse checkout enabled,
    checked out at the specific commit, and only include the specified subpath.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit="a" * 40,  # Simulating a valid commit hash
        subpath="src/docs",
    )

    with patch("gitingest.cloning.check_repo_exists", return_value=True):
        with patch("gitingest.cloning.run_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            # Verify the clone command includes sparse checkout flags
            mock_exec.assert_any_call(
                "git",
                "clone",
                "--single-branch",
                "--filter=blob:none",
                "--sparse",
                clone_config.url,
                clone_config.local_path,
            )

            # Verify the sparse-checkout command sets the correct path
            mock_exec.assert_any_call(
                "git",
                "-C",
                clone_config.local_path,
                "sparse-checkout",
                "set",
                "src/docs",
                "checkout",
                clone_config.commit,
            )

            assert mock_exec.call_count == 2


@pytest.mark.asyncio
async def test_clone_public_repo_with_token(mocker) -> None:
    """
    Test cloning a public repo with a token. check_repo_exists should be skipped.
    """
    token = "ghp_TestTokenValue12345"
    url = "https://github.com/public/repo"
    auth_url = f"https://{token}@github.com/public/repo"
    clone_config = CloneConfig(url=url, local_path="/tmp/repo")

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists")
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    await clone_repo(clone_config, access_token=token)

    mock_check.assert_not_called()
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", auth_url, clone_config.local_path
    )


@pytest.mark.asyncio
async def test_clone_private_repo_with_valid_token(mocker) -> None:
    """
    Test cloning a private repo with a valid token.
    """
    token = "ghp_ValidPrivateToken123"
    url = "https://github.com/private/repo"
    auth_url = f"https://{token}@github.com/private/repo"
    clone_config = CloneConfig(url=url, local_path="/tmp/private-repo")

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists")
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    await clone_repo(clone_config, access_token=token)

    mock_check.assert_not_called()
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", auth_url, clone_config.local_path
    )


@pytest.mark.asyncio
async def test_clone_private_repo_with_invalid_token(mocker, capsys) -> None:
    """
    Test cloning a private repo with an invalid token raises RuntimeError and doesn't log token.
    """
    token = "ghp_InvalidToken987"
    url = "https://github.com/private/repo"
    auth_url = f"https://{token}@github.com/private/repo"
    clone_config = CloneConfig(url=url, local_path="/tmp/private-repo-fail")
    error_message = "Authentication failed"

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists")
    # Mock run_command to simulate auth failure
    mock_exec = mocker.patch(
        "gitingest.cloning.run_command",
        side_effect=RuntimeError(f"Command failed: git clone ... {auth_url} ...\\nError: {error_message}")
    )

    with pytest.raises(RuntimeError, match=error_message):
        await clone_repo(clone_config, access_token=token)

    mock_check.assert_not_called()
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", auth_url, clone_config.local_path
    )

    # Check that the token is not in the captured output (from the RuntimeError)
    captured = capsys.readouterr()
    assert token not in captured.out
    assert token not in captured.err
    # Ensure the auth_url itself isn't printed verbatim in the error
    assert auth_url not in captured.out
    assert auth_url not in captured.err


@pytest.mark.asyncio
async def test_clone_private_repo_without_token(mocker) -> None:
    """
    Test cloning a private repo without a token raises ValueError.
    """
    url = "https://github.com/private/repo-no-token"
    clone_config = CloneConfig(url=url, local_path="/tmp/private-repo-no-token")

    # Mock check_repo_exists to return False, as it would for a private repo
    mock_check = mocker.patch("gitingest.cloning.check_repo_exists", return_value=False)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    with pytest.raises(ValueError, match="Repository not found or inaccessible. If private, provide a token."):
        await clone_repo(clone_config, access_token=None)

    mock_check.assert_called_once_with(url)
    mock_exec.assert_not_called()


@pytest.mark.asyncio
async def test_clone_non_github_repo_with_token(mocker) -> None:
    """
    Test cloning a non-GitHub repo with a token.
    The URL should be modified for known hosts (GitLab, Bitbucket, Codeberg).
    The existence check should be skipped.
    """
    token = "gitlab_TokenValue12345"
    url = "https://gitlab.com/public/repo"
    auth_url = f"https://oauth2:{token}@gitlab.com/public/repo" # GitLab format
    clone_config = CloneConfig(url=url, local_path="/tmp/gitlab-repo")

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists")
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    await clone_repo(clone_config, access_token=token) # Use access_token

    mock_check.assert_not_called() # check_repo_exists should be skipped for known host w/ token
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", auth_url, clone_config.local_path # Use GitLab auth URL
    )


@pytest.mark.asyncio
async def test_clone_bitbucket_repo_with_token(mocker) -> None:
    """Test cloning a Bitbucket repo with a token."""
    token = "bitbucket_token_xyz"
    url = "https://bitbucket.org/team/repo"
    auth_url = f"https://x-token-auth:{token}@bitbucket.org/team/repo"
    clone_config = CloneConfig(url=url, local_path="/tmp/bitbucket-repo")

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists")
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    await clone_repo(clone_config, access_token=token)

    mock_check.assert_not_called()
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", auth_url, clone_config.local_path
    )


@pytest.mark.asyncio
async def test_clone_codeberg_repo_with_token(mocker) -> None:
    """Test cloning a Codeberg repo with a token."""
    token = "codeberg_token_abc"
    url = "https://codeberg.org/user/repo"
    auth_url = f"https://{token}@codeberg.org/user/repo"
    clone_config = CloneConfig(url=url, local_path="/tmp/codeberg-repo")

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists")
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    await clone_repo(clone_config, access_token=token)

    mock_check.assert_not_called()
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", auth_url, clone_config.local_path
    )


@pytest.mark.asyncio
async def test_clone_unknown_host_with_token(mocker) -> None:
    """
    Test cloning an unknown host with a token.
    The URL should NOT be modified, and existence check should NOT be skipped.
    """
    token = "some_token"
    url = "https://mygitserver.com/user/repo"
    clone_config = CloneConfig(url=url, local_path="/tmp/unknown-repo")

    mock_check = mocker.patch("gitingest.cloning.check_repo_exists", return_value=True)
    mock_exec = mocker.patch("gitingest.cloning.run_command", new_callable=AsyncMock)

    await clone_repo(clone_config, access_token=token)

    mock_check.assert_called_once_with(url) # Existence check should be called
    mock_exec.assert_called_once_with(
        "git", "clone", "--single-branch", "--depth=1", url, clone_config.local_path # URL unchanged
    )
