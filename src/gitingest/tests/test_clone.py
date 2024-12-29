from unittest.mock import AsyncMock, patch

import pytest
from clone import clone_repo, check_repo_exists
from unittest.mock import patch, AsyncMock
from asyncio.exceptions import TimeoutError


@pytest.mark.asyncio
async def test_clone_repo_with_commit():
    query = {
        "commit": "a" * 40,  # Simulating a valid commit hash
        "branch": "main",
        "url": "https://github.com/joydeep049/gitingest",
        "local_path": "/tmp/repo",
    }

    with patch("clone.check_repo_exists", return_value=True) as mock_check:
        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Cloning Complete", b"")
            mock_exec.return_value = mock_process

            stdout, stdin = await clone_repo(query)

            mock_check.assert_called_once_with(query["url"])
 
            assert mock_exec.call_count == 2  # Clone and checkout calls
            assert b"Cloning Complete" in stdout



@pytest.mark.asyncio
async def test_clone_repo_without_commit():
    query = {
        "commit": None,
        "branch": "main",
        "url": "https://github.com/joydeep049/gitingest",
        "local_path": "/tmp/repo",
    }

    with patch("clone.check_repo_exists", return_value=True) as mock_check:
        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Cloning Complete", b"error")
            mock_exec.return_value = mock_process

            stdout, stderr = await clone_repo(query)

            mock_check.assert_called_once_with(query["url"])
            assert mock_exec.call_count == 1  # Only clone call
            assert b"Cloning Complete" in stdout


@pytest.mark.asyncio
async def test_clone_repo_with_branch():
    query = {
        "commit": None,
        "branch": "feature-branch",
        "url": "https://github.com/joydeep049/gitingest",
        "local_path": "/tmp/repo",
    }
    with patch("clone.check_repo_exists", return_value=True) as mock_check:
        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Branch clone successful", b"")
            mock_exec.return_value = mock_process

            stdout, stderr = await clone_repo(query)

            mock_check.assert_called_once_with(query["url"])
            assert mock_exec.call_count == 1  # Only clone
            assert b"Branch clone successful" in stdout


@pytest.mark.asyncio
async def test_clone_repo_missing_fields():
    query = {
        "branch": "main",
        "url": "https://github.com/joydeep049/gitingest",
    }  # Missing 'commit' and 'local_path'
    with pytest.raises(KeyError, match="commit"):
        await clone_repo(query)


@pytest.mark.asyncio
async def test_clone_repo_timeout():
    query = {
        "commit": None,
        "branch": "main",
        "url": "https://github.com/joydeep049/gitingest",
        "local_path": "C:\\Users\\joyde\\OneDrive\\Desktop\\project structure\\gitingest",
    }
    with patch("clone.check_repo_exists", return_value=True):
        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.side_effect = TimeoutError

            stdout, stderr = await clone_repo(query)
            assert stderr == "TimeoutError"
            assert stdout == "The repository cloning process timed out."



@pytest.mark.asyncio
async def test_clone_repo_nonexistent_repository():
    query = {
        "commit": None,
        "branch": "main",
        "url": "https://github.com/joydeep049/nonexistent-repo",
        "local_path": "/tmp/repo",
    }

    with patch("gitingest.clone.check_repo_exists", return_value=False) as mock_check:
        with pytest.raises(ValueError, match="Repository not found"):
            await clone_repo(query)
            mock_check.assert_called_once_with(query["url"])


@pytest.mark.asyncio
async def test_check_repo_exists():
    url = "https://github.com/joydeep049/gitingest"

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"HTTP/1.1 200 OK\n", b"")
        mock_exec.return_value = mock_process

        # Test existing repository
        mock_process.returncode = 0
        assert await check_repo_exists(url) is True

        # Test non-existing repository (404 response)
        mock_process.communicate.return_value = (b"HTTP/1.1 404 Not Found\n", b"")
        mock_process.returncode = 0
        assert await check_repo_exists(url) is False

        # Test failed request
        mock_process.returncode = 1
        assert await check_repo_exists(url) is False
