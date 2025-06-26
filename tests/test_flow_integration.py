"""Integration tests covering core functionalities, edge cases, and concurrency handling."""

import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest
from pytest_mock import MockerFixture

from src.server.main import app

# Set environment variable for testing to disable rate limiting
os.environ["TESTING"] = "true"

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
        "include_submodules": "false",
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
        "include_submodules": "false",
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
        "include_submodules": "false",
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
            "include_submodules": "false",
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
        "include_submodules": "false",
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
        "include_submodules": "false",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_repository_with_submodules(request: FixtureRequest) -> None:
    """
    Test repository analysis with include_submodules enabled.

    Given a repository URL and include_submodules set to True:
    When the form is submitted,
    Then the request should be processed and the mocked template should be rendered.
    """
    client = request.getfixturevalue("test_client")
    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
        "include_submodules": "true",
        "token": "",
    }

    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Request failed: {response.text}"
    assert "Mocked Template Response" in response.text


@pytest.mark.asyncio
async def test_include_submodules_true_propagation(request: FixtureRequest, mocker: MockerFixture) -> None:
    """
    Test that include_submodules='true' is correctly propagated through backend and clone_repo.

    Given a form POST with include_submodules='true':
    When the request is processed by the backend:
    Then include_submodules should be parsed as True and passed to process_query.
    """
    client = request.getfixturevalue("test_client")
    # Patch clone_repo and parse_query where they are used in the server
    clone_repo_mock = mocker.patch("server.query_processor.clone_repo", autospec=True, return_value=None)
    parse_query_orig = __import__("gitingest.query_parsing", fromlist=["parse_query"]).parse_query
    captured_query = {}

    async def parse_query_capture(*args, **kwargs):
        result = await parse_query_orig(*args, **kwargs)
        captured_query["query"] = result
        return result

    mocker.patch("server.query_processor.parse_query", side_effect=parse_query_capture)

    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
        "include_submodules": "true",
        "token": "",
    }
    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Form submission failed: {response.text}"
    assert "Mocked Template Response" in response.text
    # Check that parse_query was called and include_submodules is True
    assert "query" in captured_query, "parse_query was not called"
    assert getattr(captured_query["query"], "include_submodules", None) is True
    # Check that clone_repo was called with include_submodules True
    assert clone_repo_mock.called, "clone_repo was not called"
    clone_config = clone_repo_mock.call_args[0][0]
    assert getattr(clone_config, "include_submodules", None) is True


@pytest.mark.asyncio
async def test_include_submodules_false_propagation(request: FixtureRequest, mocker: MockerFixture) -> None:
    """
    Test that include_submodules='false' is correctly propagated through backend and clone_repo.

    Given a form POST with include_submodules='false':
    When the request is processed by the backend:
    Then include_submodules should be parsed as False and passed to process_query.
    """
    client = request.getfixturevalue("test_client")
    clone_repo_mock = mocker.patch("server.query_processor.clone_repo", autospec=True, return_value=None)
    parse_query_orig = __import__("gitingest.query_parsing", fromlist=["parse_query"]).parse_query
    captured_query = {}

    async def parse_query_capture(*args, **kwargs):
        result = await parse_query_orig(*args, **kwargs)
        captured_query["query"] = result
        return result

    mocker.patch("server.query_processor.parse_query", side_effect=parse_query_capture)

    form_data = {
        "input_text": "https://github.com/octocat/Hello-World",
        "max_file_size": "243",
        "pattern_type": "exclude",
        "pattern": "",
        "include_submodules": "false",
        "token": "",
    }
    response = client.post("/", data=form_data)
    assert response.status_code == 200, f"Form submission failed: {response.text}"
    assert "Mocked Template Response" in response.text
    assert "query" in captured_query, "parse_query was not called"
    assert getattr(captured_query["query"], "include_submodules", None) is False
    assert clone_repo_mock.called, "clone_repo was not called"
    clone_config = clone_repo_mock.call_args[0][0]
    assert getattr(clone_config, "include_submodules", None) is False
