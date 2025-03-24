"""
Tests for API response formats.

These tests verify that the API correctly returns responses in different formats
based on the format parameter or Accept header.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.server.main import app


@pytest.fixture(scope="module")
def test_client():
    """Create a test client fixture."""
    with TestClient(app) as client_instance:
        client_instance.headers.update({"Host": "localhost"})
        yield client_instance


@pytest.fixture(scope="module", autouse=True)
def mock_static_files():
    """Mock the static file mount to avoid directory errors."""
    with patch("src.server.main.StaticFiles") as mock_static:
        mock_static.return_value = None  # Mocks the StaticFiles response
        yield mock_static


@pytest.fixture(scope="module", autouse=True)
def mock_templates():
    """Mock Jinja2 template rendering to bypass actual file loading."""
    with patch("starlette.templating.Jinja2Templates.TemplateResponse") as mock_template:
        mock_template.return_value = "Mocked Template Response"
        yield mock_template


@pytest.fixture(scope="function")
def mock_process_query():
    """Mock the process_query function to return predictable results."""
    with patch("src.server.routers.dynamic.process_query") as mock_query:
        # Create a mock response with test data
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Set up the mock to return different responses based on format
        async def side_effect(*args, **kwargs):
            response_format = kwargs.get("response_format", "text")
            
            if response_format == "json":
                mock_response.media_type = "application/json"
                mock_response.body = json.dumps({
                    "summary": "Test summary",
                    "tree": "Test tree",
                    "content": "Test content",
                    "ingest_id": "test-id"
                }).encode()
            else:  # text
                mock_response.media_type = "text/plain"
                mock_response.body = "Test summary\n\nTest tree\n\nTest content".encode()
            
            return mock_response
        
        mock_query.side_effect = side_effect
        yield mock_query


@pytest.mark.asyncio
async def test_text_format_with_parameter(request, mock_process_query):
    """Test that the API returns plain text when format=text is specified."""
    client = request.getfixturevalue("test_client")
    
    # Set User-Agent to a non-browser value
    headers = {"User-Agent": "curl/7.68.0"}
    
    response = client.get("/octocat/Hello-World?format=text", headers=headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "Test summary" in response.text
    assert "Test tree" in response.text
    assert "Test content" in response.text


@pytest.mark.asyncio
async def test_json_format_with_parameter(request, mock_process_query):
    """Test that the API returns JSON when format=json is specified."""
    client = request.getfixturevalue("test_client")
    
    # Set User-Agent to a non-browser value
    headers = {"User-Agent": "curl/7.68.0"}
    
    response = client.get("/octocat/Hello-World?format=json", headers=headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert data["summary"] == "Test summary"
    assert data["tree"] == "Test tree"
    assert data["content"] == "Test content"
    assert data["ingest_id"] == "test-id"


@pytest.mark.asyncio
async def test_json_format_with_accept_header(request, mock_process_query):
    """Test that the API returns JSON when Accept: application/json is specified."""
    client = request.getfixturevalue("test_client")
    
    # Set User-Agent to a non-browser value and Accept header to application/json
    headers = {
        "User-Agent": "curl/7.68.0",
        "Accept": "application/json"
    }
    
    response = client.get("/octocat/Hello-World", headers=headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert data["summary"] == "Test summary"
    assert data["tree"] == "Test tree"
    assert data["content"] == "Test content"
    assert data["ingest_id"] == "test-id"


@pytest.mark.asyncio
async def test_format_parameter_overrides_accept_header(request, mock_process_query):
    """Test that the format parameter takes precedence over the Accept header."""
    client = request.getfixturevalue("test_client")
    
    # Set User-Agent to a non-browser value, Accept header to text/plain,
    # but format parameter to json
    headers = {
        "User-Agent": "curl/7.68.0",
        "Accept": "text/plain"
    }
    
    response = client.get("/octocat/Hello-World?format=json", headers=headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert data["summary"] == "Test summary"
    assert data["tree"] == "Test tree"
    assert data["content"] == "Test content"
    assert data["ingest_id"] == "test-id"


@pytest.mark.asyncio
async def test_browser_request_ignores_format_parameter(request):
    """Test that browser requests ignore the format parameter and return HTML."""
    client = request.getfixturevalue("test_client")
    
    # Set User-Agent to a browser value
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    response = client.get("/octocat/Hello-World?format=json", headers=headers)
    
    assert response.status_code == 200
    assert "Mocked Template Response" in response.text
