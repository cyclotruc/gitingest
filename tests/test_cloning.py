"""Tests for the cloning module functionality."""

from gitingest.cloning import build_auth_url


class TestBuildAuthUrl:
    """Test cases for the build_auth_url function."""

    def test_no_token_returns_original_url(self):
        """Test that when no token is provided, the original URL is returned."""
        url = "https://github.com/owner/repo.git"
        assert build_auth_url(url) == url
        assert build_auth_url(url, None) == url

    def test_github_auth_url(self):
        """Test GitHub URL authentication with prefix method."""
        url = "https://github.com/owner/repo.git"
        token = "ghp_1234abcd"
        expected = "https://ghp_1234abcd@github.com/owner/repo.git"
        assert build_auth_url(url, token) == expected

    def test_gitlab_auth_url(self):
        """Test GitLab URL authentication with oauth2 method."""
        url = "https://gitlab.com/owner/repo.git"
        token = "glpat-1234abcd"
        expected = "https://oauth2:glpat-1234abcd@gitlab.com/owner/repo.git"
        assert build_auth_url(url, token) == expected

    def test_bitbucket_auth_url(self):
        """Test Bitbucket URL authentication with prefix method and custom user."""
        url = "https://bitbucket.org/owner/repo.git"
        token = "1234abcd"
        expected = "https://x-token-auth:1234abcd@bitbucket.org/owner/repo.git"
        assert build_auth_url(url, token) == expected

    def test_codeberg_auth_url(self):
        """Test Codeberg URL authentication with prefix method."""
        url = "https://codeberg.org/owner/repo.git"
        token = "1234abcd"
        expected = "https://1234abcd@codeberg.org/owner/repo.git"
        assert build_auth_url(url, token) == expected

    def test_unknown_host(self):
        """Test that unknown hosts return the original URL."""
        url = "https://unknown-git-host.com/owner/repo.git"
        token = "1234abcd"
        assert build_auth_url(url, token) == url

    def test_case_insensitive_hostname(self):
        """Test that hostname matching is case-insensitive."""
        url = "https://GitHub.com/owner/repo.git"
        token = "1234abcd"
        expected = "https://1234abcd@GitHub.com/owner/repo.git"
        assert build_auth_url(url, token) == expected

    def test_invalid_url(self, capfd):
        """Test handling of invalid URLs."""
        url = "not-a-valid-url"
        token = "1234abcd"
        result = build_auth_url(url, token)

        # Check that a warning was printed
        out, _ = capfd.readouterr()
        assert "Warning: Could not parse URL" in out
        assert result == url
