import pytest
from clone import clone_repo, check_repo_exists
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_clone_repo_with_commit():
    query = {
        'commit': 'a' * 40,  # Simulating a valid commit hash
        'branch': 'main',
        'url': 'https://github.com/user/repo',
        'local_path': '/tmp/repo'
    }
    
    with patch('clone.check_repo_exists', return_value=True) as mock_check:
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b'output', b'error')
            mock_exec.return_value = mock_process
            
            await clone_repo(query)
            mock_check.assert_called_once_with(query['url'])
            assert mock_exec.call_count == 2  # Clone and checkout calls

@pytest.mark.asyncio
async def test_clone_repo_without_commit():
    query = {
        'commit': None,
        'branch': 'main',
        'url': 'https://github.com/user/repo',
        'local_path': '/tmp/repo'
    }
    
    with patch('clone.check_repo_exists', return_value=True) as mock_check:
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b'output', b'error')
            mock_exec.return_value = mock_process
            
            await clone_repo(query)
            mock_check.assert_called_once_with(query['url'])
            assert mock_exec.call_count == 1  # Only clone call

@pytest.mark.asyncio
async def test_clone_repo_nonexistent_repository():
    query = {
        'commit': None,
        'branch': 'main',
        'url': 'https://github.com/user/nonexistent-repo',
        'local_path': '/tmp/repo'
    }
    
    with patch('gitingest.clone.check_repo_exists', return_value=False) as mock_check:
        with pytest.raises(ValueError, match="Repository not found"):
            await clone_repo(query)
            mock_check.assert_called_once_with(query['url'])

@pytest.mark.asyncio
async def test_check_repo_exists():
    url = "https://github.com/user/repo"
    
    with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'HTTP/1.1 200 OK\n', b'')
        mock_exec.return_value = mock_process
        
        # Test existing repository
        mock_process.returncode = 0
        assert await check_repo_exists(url) is True
        
        # Test non-existing repository (404 response)
        mock_process.communicate.return_value = (b'HTTP/1.1 404 Not Found\n', b'')
        mock_process.returncode = 0
        assert await check_repo_exists(url) is False

        # Test failed request
        mock_process.returncode = 1
        assert await check_repo_exists(url) is False