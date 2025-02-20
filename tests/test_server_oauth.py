import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from authlib.integrations.starlette_client import OAuthError
from server.main import app


@pytest.fixture
def client():
    """
    Provide a TestClient instance for our FastAPI application.
    Make sure we've added "testserver" or "localhost" to the TrustedHostMiddleware,
    or use base_url that matches an allowed host.
    """
    return TestClient(app, base_url="http://localhost")


def test_login_redirect(client):
    """
    Test GET /oauth/login: we patch authorize_redirect and confirm it's called,
    then check we got some response that includes the "mocked redirect response".
    """
    with patch("server.oauth.oauth.github.authorize_redirect") as mock_redirect:
        # Instead of returning a string, let's return an actual starlette response
        from starlette.responses import PlainTextResponse
        mock_redirect.return_value = PlainTextResponse("mocked redirect response")

        response = client.get("/oauth/login", follow_redirects=False)

        mock_redirect.assert_called_once()

        assert response.status_code == 200

        assert "mocked redirect response" in response.text


def test_auth_success(client):
    fake_token = {"access_token": "ABC123"}
    with patch("server.oauth.oauth.github.authorize_access_token") as mock_access_token, \
        patch("server.oauth.oauth.github.get", new_callable=AsyncMock) as mock_github_get:
        mock_access_token.return_value = fake_token

        user_resp = AsyncMock()
        user_resp.json = MagicMock(return_value={"login": "testuser", "id": 1234})
        mock_github_get.return_value = user_resp

        response = client.get("/oauth/auth", follow_redirects=False)

        mock_access_token.assert_called_once()
        mock_github_get.assert_called_once_with("user", token=fake_token)
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/"


def test_auth_failure(client):
    """
    If authorize_access_token raises OAuthError, we expect a 400 error.
    """
    with patch("server.oauth.oauth.github.authorize_access_token", side_effect=OAuthError("invalid_grant")):
        response = client.get("/oauth/auth", follow_redirects=False)
        assert response.status_code == 400

        assert "invalid_grant" in response.text


def test_logout(client):
    """
    Test GET /oauth/logout.
    We'll assume it unsets the session key and redirects to "/".
    """
    # Add a fake session cookie if needed:
    client.cookies.set("session", "fake-session-value")

    response = client.get("/oauth/logout", follow_redirects=False)
    # Should redirect
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/"
