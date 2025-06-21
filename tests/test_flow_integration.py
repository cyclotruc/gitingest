"""Integration tests covering core functionalities, edge cases, and concurrency handling."""

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest
from pytest_mock import MockerFixture

from src.server.main import app

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "src" / "templates"


@pytest.fixture(scope="module")
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client fixture."""
    with TestClient(app) as client_instance:
        client_instance.headers.update({"Host": "localhost"})
        yield client_instance


@pytest.fixture(autouse=True)
def mock_static_files(mocker: MockerFixture) -> Generator[None, None, None]:
    """Mock the static file mount to avoid directory errors."""
    mock_static = mocker.patch("src.server.main.StaticFiles", autospec=True)
    mock_static.return_value = None
    yield mock_static


@pytest.fixture(autouse=True)
def mock_templates(mocker: MockerFixture) -> Generator[None, None, None]:
    """Mock Jinja2 template rendering to bypass actual file loading."""
    mock_template = mocker.patch("starlette.templating.Jinja2Templates.TemplateResponse", autospec=True)
    mock_template.return_value = "Mocked Template Response"
    yield mock_template


@pytest.fixture(scope="module", autouse=True)
def cleanup_tmp_dir() -> Generator[None, None, None]:
    """Remove /tmp/gitingest after this test-module is done."""
    yield  # run tests
    temp_dir = Path("/tmp/gitingest")
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except PermissionError as exc:
            print(f"Error cleaning up {temp_dir}: {exc}")


@pytest.mark.asyncio
async def test_remote_repository_analysis(request: FixtureRequest) -> None:
    """Test the complete flow of analyzing a remote repository."""
    client = request.getfixturevalue("test_client")
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Form submission failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_invalid_repository_url(request: FixtureRequest) -> None:
    """Test handling of an invalid repository URL."""
    client = request.getfixturevalue("test_client")
    form_data = {
        "input_text": "https://github.com/nonexistent/repo",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_large_repository(request: FixtureRequest) -> None:
    """Simulate analysis of a large repository with nested folders."""
    client = request.getfixturevalue("test_client")
    form_data = {
        "input_text": "https://github.com/large/repo-with-many-files",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_concurrent_requests(request: FixtureRequest) -> None:
    """Test handling of multiple concurrent requests."""
    client = request.getfixturevalue("test_client")

    def make_request():
        form_data = {
            "input_text": "https://github.com/octocat/Hello-World",
            "max_file_size": "243",
            "pattern_type": "exclude",
            "pattern": "",
            "token": "",
        }
        response = client.post("/", data=form_data)
        assert response.status_code == 200, f"Request failed: {response.text}"
        assert "Mocked Template Response" in response.text

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        for future in futures:
            future.result()


@pytest.mark.asyncio
async def test_large_file_handling(request: FixtureRequest) -> None:
    """Test handling of repositories with large files."""
    client = request.getfixturevalue("test_client")
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "1",
        "pattern_type": "exclude",
        "pattern": "",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_repository_with_patterns(request: FixtureRequest) -> None:
    """Test repository analysis with include/exclude patterns."""
    client = request.getfixturevalue("test_client")
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "include",
        "pattern": "*.md",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text
