import pytest
from utils.clone import clone_repo
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_clone_repo_with_commit():
    query = {
        'commit': 'a' * 40,  # Simulating a valid commit hash
        'branch': 'main',
        'url': 'https://github.com/user/repo',
        'local_path': '/tmp/repo'
    }
    with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
        await clone_repo(query)
        assert mock_exec.call_count == 2  # Ensure both clone and checkout are called

@pytest.mark.asyncio
async def test_clone_repo_without_commit():
    query = {
        'commit': None,
        'branch': 'main',
        'url': 'https://github.com/user/repo',
        'local_path': '/tmp/repo'
    }
    with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
        await clone_repo(query)
        assert mock_exec.call_count == 1  # Ensure only clone is called