from unittest.mock import AsyncMock, patch

import pytest

from gitingest.clone import CloneConfig, _check_repo_exists, clone_repo


@pytest.mark.asyncio
async def test_clone_repo_with_commit() -> None:
    clone_config = CloneConfig(
        url="https://github.com/user/repo",
        local_path="/tmp/repo",
        commit="a" * 40,  # Simulating a valid commit hash
        branch="main",
    )

    with patch("gitingest.clone._check_repo_exists", return_value=True) as mock_check:
        with patch("gitingest.clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"error")
            mock_exec.return_value = mock_process

            await clone_repo(clone_config)
            mock_check.assert_called_once_with(clone_config.url, None)
            assert mock_exec.call_count == 2  # Clone and checkout calls


@pytest.mark.asyncio
async def test_clone_repo_without_commit() -> None:
    clone_config = CloneConfig(url="https://github.com/user/repo", local_path="/tmp/repo", commit=None, branch="main")

    with patch("gitingest.clone._check_repo_exists", return_value=True) as mock_check:
        with patch("gitingest.clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"error")
            mock_exec.return_value = mock_process

            await clone_repo(clone_config)
            mock_check.assert_called_once_with(clone_config.url, None)
            assert mock_exec.call_count == 1  # Only clone call


@pytest.mark.asyncio
async def test_clone_repo_nonexistent_repository() -> None:
    clone_config = CloneConfig(
        url="https://github.com/user/nonexistent-repo",
        local_path="/tmp/repo",
        commit=None,
        branch="main",
    )
    with patch("gitingest.clone._check_repo_exists", return_value=False) as mock_check:
        with pytest.raises(ValueError, match="Repository not found"):
            await clone_repo(clone_config)
            mock_check.assert_called_once_with(clone_config.url, None)


@pytest.mark.asyncio
async def test_check_repo_exists() -> None:
    url = "https://github.com/user/repo"

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 200 OK\n", b"")
        mock_exec.return_value = mock_process

        # Test existing repository
        mock_process.returncode = 0
        assert await _check_repo_exists(url) is True

        # Test non-existing repository (404 response)
        mock_process.communicate.return_value = (b"HTTP/1.1 404 Not Found\n", b"")
        mock_process.returncode = 0
        assert await _check_repo_exists(url) is False

        # Test failed request
        mock_process.returncode = 1
        assert await _check_repo_exists(url) is False


@pytest.mark.asyncio
async def test_check_repo_exists_with_pat() -> None:
    url = "https://github.com/user/repo"
    pat = "test_token_123"

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 200 OK\n", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        await _check_repo_exists(url, pat)

        # Verify curl command includes authorization header
        mock_exec.assert_called_with(
            "curl",
            "-I",
            "-H",
            f"Authorization: token {pat}",
            url,
            stdout=-1,  # asyncio.subprocess.PIPE
            stderr=-1,  # asyncio.subprocess.PIPE
        )


@pytest.mark.asyncio
async def test_check_repo_exists_custom_git_server() -> None:
    url = "https://git.custom.com/user/repo"
    pat = "test_token_123"

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 200 OK\n", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        await _check_repo_exists(url, pat)

        # Verify curl command uses correct API endpoint and includes authorization header
        mock_exec.assert_called_with(
            "curl",
            "-I",
            "-H",
            f"Authorization: token {pat}",
            "https://git.custom.com/api/v1/repos/user/repo",
            stdout=-1,  # asyncio.subprocess.PIPE
            stderr=-1,  # asyncio.subprocess.PIPE
        )


@pytest.mark.asyncio
async def test_clone_repo_with_pat() -> None:
    clone_config = CloneConfig(
        url="https://git.custom.com/user/repo",
        local_path="/tmp/repo",
        commit=None,
        branch="main",
        pat="test_token_123",
    )

    with patch("gitingest.clone._check_repo_exists", return_value=True) as mock_check:
        with patch("gitingest.clone._run_git_command", new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"error")
            mock_exec.return_value = mock_process

            await clone_repo(clone_config)
            mock_check.assert_called_once_with(clone_config.url, clone_config.pat)

            # Verify git clone command includes PAT in URL
            expected_url = clone_config.url.replace("https://", f"https://oauth2:{clone_config.pat}@")
            # Check that the command was called with the correct arguments
            mock_exec.assert_called_with(
                "git", "clone", "--depth=1", "--single-branch", expected_url, clone_config.local_path
            )
