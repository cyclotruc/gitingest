import pytest

from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS
from gitingest.parse_query import parse_query, parse_url


def test_parse_url_valid() -> None:
    test_cases = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo",
        "https://bitbucket.org/user/repo",
    ]
    for url in test_cases:
        result = parse_url(url)
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["url"] == url


def test_parse_url_invalid() -> None:
    url = "https://only-domain.com"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        parse_url(url)


def test_parse_query_basic() -> None:
    test_cases = ["https://github.com/user/repo", "https://gitlab.com/user/repo"]
    for url in test_cases:
        result = parse_query(url, max_file_size=50, from_web=True, ignore_patterns="*.txt")
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["url"] == url
        assert "*.txt" in result["ignore_patterns"]


def test_parse_query_include_pattern() -> None:
    url = "https://github.com/user/repo"
    result = parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py")
    assert result["include_patterns"] == ["*.py"]
    assert set(result["ignore_patterns"]) == set(DEFAULT_IGNORE_PATTERNS)


def test_parse_query_invalid_pattern() -> None:
    url = "https://github.com/user/repo"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py;rm -rf")
