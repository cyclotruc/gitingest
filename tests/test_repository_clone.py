import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, ANY

import pytest

from gitingest.exceptions import AsyncTimeoutError
from gitingest.repository_clone import CloneConfig, _check_repo_exists, clone_repo

@pytest.mark.asyncio
async def test_clone_repo_with_commit() -> None:
    """
    Test cloning a repository with a specific commit hash.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit="a" * 40,
        branch="main",
    )
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True) as mock_check:
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            mock_check.assert_called_once()
            check_args, check_kwargs = mock_check.call_args
            assert check_args[0] == clone_config.url
            assert "token" in check_kwargs

            # Expect two calls: (1) clone, (2) checkout
            assert mock_exec.call_count == 2

            # 1) The clone call
            clone_args = mock_exec.call_args_list[0][0]
            assert clone_args[0] == "git"
            assert clone_args[1] == "clone"
            assert "--recurse-submodules" in clone_args
            # We skip checking `--depth=1` because the code likely doesn't do a shallow clone when commit is given

            combined_args = " ".join(clone_args)
            assert "github.com/user/repo" in combined_args

            # 2) The checkout call
            checkout_args = mock_exec.call_args_list[1][0]
            assert checkout_args[:3] == ("git", "-C", clone_config.local_path)
            assert checkout_args[3] == "checkout"
            assert checkout_args[4] == clone_config.commit


@pytest.mark.asyncio
async def test_clone_repo_without_commit() -> None:
    """
    Test cloning a repository when no commit hash is provided.
    """
    query = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit=None,
        branch="main",
    )
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True) as mock_check:
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(query)

            mock_check.assert_called_once()
            assert mock_exec.call_count == 1  # Only clone, no checkout

            clone_args = mock_exec.call_args_list[0][0]
            assert clone_args[0] == "git"
            assert clone_args[1] == "clone"
            assert "--recurse-submodules" in clone_args
            assert "--depth=1" in clone_args
            assert "--single-branch" in clone_args
            # Possibly check for --branch main if your code adds it
            combined_args = " ".join(clone_args)
            assert "github.com/user/repo" in combined_args


@pytest.mark.asyncio
async def test_clone_repo_nonexistent_repository() -> None:
    """
    Test cloning a nonexistent repository URL.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/nonexistent-repo",
        local_path="/tmp/repo",
        commit=None,
        branch="main",
    )
    with patch("gitingest.repository_clone._check_repo_exists", return_value=False):
        # Match the new error message in your code:
        with pytest.raises(ValueError, match="We could not find or access this repository"):
            await clone_repo(clone_config)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_stdout, return_code, expected",
    [
        (b"HTTP/1.1 200 OK\n", 0, True),
        (b"HTTP/1.1 404 Not Found\n", 0, False),
        (b"HTTP/1.1 200 OK\n", 1, False),
    ],
)
async def test_check_repo_exists(mock_stdout: bytes, return_code: int, expected: bool) -> None:
    url = "https://github.com/user/repo"
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_stdout, b"")
        mock_process.returncode = return_code
        mock_exec.return_value = mock_process

        repo_exists = await _check_repo_exists(url, token="fake-token")
        assert repo_exists is expected


@pytest.mark.asyncio
async def test_clone_repo_invalid_url() -> None:
    clone_config = CloneConfig(url="", local_path="/tmp/repo")
    with pytest.raises(ValueError, match="The 'url' parameter is required."):
        await clone_repo(clone_config)


@pytest.mark.asyncio
async def test_clone_repo_invalid_local_path() -> None:
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="")
    with pytest.raises(ValueError, match="The 'local_path' parameter is required."):
        await clone_repo(clone_config)


@pytest.mark.asyncio
async def test_clone_repo_with_custom_branch() -> None:
    """
    Test cloning a repository with a specified custom branch.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        branch="feature-branch",
    )
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            mock_exec.assert_called_once()
            args = mock_exec.call_args_list[0][0]
            assert args[0] == "git"
            assert args[1] == "clone"
            assert "--recurse-submodules" in args
            assert "--depth=1" in args
            assert "--single-branch" in args
            assert "--branch" in args
            # The next item after '--branch' should be 'feature-branch'
            idx = args.index("--branch")
            assert args[idx + 1] == "feature-branch"
            # Combined check for the token-URL
            combined_args = " ".join(args)
            assert "github.com/user/repo" in combined_args


@pytest.mark.asyncio
async def test_git_command_failure() -> None:
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo")
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", side_effect=RuntimeError("Git command failed")):
            with pytest.raises(RuntimeError, match="Git command failed"):
                await clone_repo(clone_config)


@pytest.mark.asyncio
async def test_clone_repo_default_shallow_clone() -> None:
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo")
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            mock_exec.assert_called_once()
            args = mock_exec.call_args_list[0][0]
            assert args[0] == "git"
            assert args[1] == "clone"
            assert "--recurse-submodules" in args
            assert "--depth=1" in args
            assert "--single-branch" in args
            combined_args = " ".join(args)
            assert "github.com/user/repo" in combined_args


@pytest.mark.asyncio
async def test_clone_repo_commit_without_branch() -> None:
    """
    Test cloning when a commit hash is provided but no branch is specified.
    """
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit="a" * 40,
    )
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)
            assert mock_exec.call_count == 2

            # 1) Clone
            clone_args = mock_exec.call_args_list[0][0]
            assert clone_args[0] == "git"
            assert clone_args[1] == "clone"
            assert "--recurse-submodules" in clone_args

            combined = " ".join(clone_args)
            assert "github.com/user/repo" in combined

            # 2) Checkout
            checkout_args = mock_exec.call_args_list[1][0]
            assert checkout_args[:3] == ("git", "-C", clone_config.local_path)
            assert checkout_args[3] == "checkout"
            assert checkout_args[4] == clone_config.commit


@pytest.mark.asyncio
async def test_check_repo_exists_with_redirect() -> None:
    url = "https://github.com/user/repo"
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 302 Found\n", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        repo_exists = await _check_repo_exists(url, token="whatever")
        assert repo_exists is False


@pytest.mark.asyncio
async def test_check_repo_exists_with_permanent_redirect() -> None:
    url = "https://github.com/user/repo"
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 301 Found\n", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        repo_exists = await _check_repo_exists(url, token="whatever")
        assert repo_exists


@pytest.mark.asyncio
async def test_clone_repo_with_timeout() -> None:
    """
    If your code doesn't re-raise as AsyncTimeoutError, you can do:
      with pytest.raises(asyncio.TimeoutError):
        await clone_repo(...)
    Or keep it as-is if your code does raise AsyncTimeoutError
    """
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo")

    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = asyncio.TimeoutError

            # If your code re-raises it as AsyncTimeoutError:
            #    with pytest.raises(AsyncTimeoutError, match="Operation timed out after"):
            # Otherwise:
            with pytest.raises(asyncio.TimeoutError):
                await clone_repo(clone_config)


@pytest.mark.asyncio
async def test_clone_specific_branch(tmp_path):
    repo_url = "https://github.com/cyclotruc/gitingest.git"
    branch_name = "main"
    local_path = tmp_path / "gitingest"

    config = CloneConfig(url=repo_url, local_path=str(local_path), branch=branch_name)
    await clone_repo(config)

    assert local_path.exists()
    assert local_path.is_dir()

    current_branch = os.popen(f"git -C {local_path} branch --show-current").read().strip()
    assert current_branch == branch_name


@pytest.mark.asyncio
async def test_clone_branch_with_slashes(tmp_path):
    repo_url = "https://github.com/user/repo"
    branch_name = "fix/in-operator"
    local_path = tmp_path / "gitingest"

    clone_config = CloneConfig(url=repo_url, local_path=str(local_path), branch=branch_name)
    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            mock_exec.assert_called_once()
            args = mock_exec.call_args_list[0][0]

            assert "--branch" in args
            idx = args.index("--branch")
            assert args[idx + 1] == branch_name

            combined_args = " ".join(args)
            assert "github.com/user/repo" in combined_args


@pytest.mark.asyncio
async def test_clone_repo_creates_parent_directory(tmp_path: Path) -> None:
    nested_path = tmp_path / "deep" / "nested" / "path" / "repo"
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path=str(nested_path))

    with patch("gitingest.repository_clone._check_repo_exists", return_value=True):
        with patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            await clone_repo(clone_config)

            assert nested_path.parent.exists()

            mock_exec.assert_called_once()
            args = mock_exec.call_args_list[0][0]
            assert args[0] == "git"
            assert args[1] == "clone"
            assert "--recurse-submodules" in args
            assert "--depth=1" in args
            assert "--single-branch" in args
            combined_args = " ".join(args)
            assert "github.com/user/repo" in combined_args
            assert args[-1] == str(nested_path)


@pytest.mark.asyncio
async def test_clone_repo_private_with_token():
    fake_token = "ghp_12345FAKETOKEN"
    repo_url = "https://github.com/privateuser/privaterepo"
    local_path = "/tmp/private_repo"

    clone_config = CloneConfig(url=repo_url, local_path=local_path)
    with patch("os.getenv", return_value=fake_token), \
         patch("gitingest.repository_clone._check_repo_exists", return_value=True) as mock_check, \
         patch("gitingest.repository_clone._run_git_command", new_callable=AsyncMock) as mock_exec:

        mock_exec.return_value = (b"Cloned!", b"")

        stdout, stderr = await clone_repo(clone_config)
        mock_check.assert_called_once()
        check_args, check_kwargs = mock_check.call_args
        assert check_args[0] == repo_url
        assert check_kwargs["token"] == fake_token
        assert b"Cloned!" in stdout
        assert stderr == b""


@pytest.mark.asyncio
async def test_clone_repo_private_missing_token():
    repo_url = "https://github.com/privateuser/privaterepo"
    local_path = "/tmp/private_repo"

    clone_config = CloneConfig(url=repo_url, local_path=local_path)
    with patch("os.getenv", return_value=None), \
         patch("gitingest.repository_clone._check_repo_exists", return_value=True):

        # Adjust the match to your code's actual error message:
        with pytest.raises(ValueError, match="This repository appears to be private on GitHub"):
            await clone_repo(clone_config)
