import pytest
from gitingest.parse_query import parse_query, parse_url, DEFAULT_IGNORE_PATTERNS

URL = "https://github.com/joydeep049/gitingest"
USER = "joydeep049"
REPO = "gitingest"


def test_parse_url_valid():
    test_cases = [
        URL,
        # "https://gitlab.com/user/repo",
        # "https://bitbucket.org/user/repo"
    ]
    for url in test_cases:
        result = parse_url(url)
        assert result["user_name"] == USER
        assert result["repo_name"] == REPO
        assert result["url"] == url


def test_parse_url_invalid():
    invalid_urls = [
        "https://www.github.com",
        "invalid_url_without_protocol",
        "https://github.com/joydeep049",
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError, match="Invalid repository URL"):
            parse_url(url)


def test_parse_query_basic():
    test_cases = [
        URL,
        # "https://gitlab.com/user/repo"
    ]
    for url in test_cases:
        result = parse_query(
            url, max_file_size=50, from_web=True, ignore_patterns="*.txt"
        )
        assert result["user_name"] == USER
        assert result["repo_name"] == REPO
        assert result["url"] == url
        assert "*.txt" in result["ignore_patterns"]


def test_parse_query_include_pattern():
    url = URL
    result = parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py")
    assert result["include_patterns"] == ["*.py"]
    assert result["ignore_patterns"] == DEFAULT_IGNORE_PATTERNS


def test_parse_query_invalid_pattern():
    url = URL
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        parse_query(
            url, max_file_size=50, from_web=True, include_patterns="*.py;rm -rf"
        )


def test_parse_query_large_file_size():
    url = URL
    result = parse_query(url, max_file_size=10**9, from_web=True)
    assert result["max_file_size"] == 10**9
    assert result["url"] == url


def test_parse_query_combined_patterns():
    url = URL
    result = parse_query(
        url,
        max_file_size=50,
        from_web=True,
        include_patterns="*.py",
        ignore_patterns="*.txt",
    )
    assert "*.py" in result["include_patterns"]
    assert "*.txt" in result["ignore_patterns"]
