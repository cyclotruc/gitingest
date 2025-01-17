"""
Integration tests for GitIngest.
These tests cover core functionalities, edge cases, and concurrency handling.
"""

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "src" / "templates"


@pytest.fixture(scope="module")
def test_client():
    """Create a test client fixture."""
    with TestClient(app) as client:
        client.headers.update({"Host": "localhost"})
        yield client


@pytest.fixture(scope="module", autouse=True)
def mock_templates():
    """Mock Jinja2 template rendering to bypass actual file loading."""
    with patch("starlette.templating.Jinja2Templates.TemplateResponse") as mock_template:
        mock_template.return_value = "Mocked Template Response"
        yield mock_template


def cleanup_temp_directories():
    temp_dir = Path("/tmp/gitingest")
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except PermissionError as e:
            print(f"Error cleaning up {temp_dir}: {e}")


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup temporary directories after tests."""
    yield
    cleanup_temp_directories()


@pytest.mark.asyncio
async def test_remote_repository_analysis(test_client):  # pylint: disable=redefined-outer-name
    """Test the complete flow of analyzing a remote repository."""
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
    }

    response = test_client.post("/", data=form_data)
    assert response.status_code == 200, f"Form submission failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_invalid_repository_url(test_client):  # pylint: disable=redefined-outer-name
    """Test handling of an invalid repository URL."""
    form_data = {
        "input_text": "https://github.com/nonexistent/repo",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
    }

    response = test_client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_large_repository(test_client):  # pylint: disable=redefined-outer-name
    """Simulate analysis of a large repository with nested folders."""
    form_data = {
        "input_text": "https://github.com/large/repo-with-many-files",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
    }

    response = test_client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_concurrent_requests(test_client):  # pylint: disable=redefined-outer-name
    """Test handling of multiple concurrent requests."""

    def make_request():
        form_data = {
            "input_text": "https://github.com/octocat/Hello-World",
            "max_file_size": "243",
            "pattern_type": "exclude",
            "pattern": "",
        }
        response = test_client.post("/", data=form_data)
        assert response.status_code == 200, f"Request failed: {response.text}"
        assert "Mocked Template Response" in response.text

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        for future in futures:
            future.result()


@pytest.mark.asyncio
async def test_large_file_handling(test_client):  # pylint: disable=redefined-outer-name
    """Test handling of repositories with large files."""
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "1",
        "pattern_type": "exclude",
        "pattern": "",
    }

    response = test_client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_repository_with_patterns(test_client):  # pylint: disable=redefined-outer-name
    """Test repository analysis with include/exclude patterns."""
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "include",
        "pattern": "*.md",
    }

    response = test_client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text
