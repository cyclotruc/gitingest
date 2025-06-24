from unittest.mock import patch

from fastapi.testclient import TestClient

from src.server.main import app

def test_static_path_traversal():
    with patch("starlette.templating.Jinja2Templates.TemplateResponse"):
        with TestClient(app, headers={"host": "localhost"}) as client:
            response = client.get("/static/../pyproject.toml")
            assert response.status_code == 200

