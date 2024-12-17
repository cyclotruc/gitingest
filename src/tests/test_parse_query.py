import pytest
from utils.parse_query import parse_query, parse_url
from config import DEFAULT_IGNORE_PATTERNS


def test_parse_url_valid():
    test_cases = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo", 
        "https://bitbucket.org/user/repo"
    ]
    for url in test_cases:
        result = parse_url(url)
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["url"] == url

def test_parse_url_invalid():
    url = "https://only-domain.com"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        parse_url(url)

def test_parse_query_basic():
    test_cases = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo"
    ]
    for url in test_cases:
        result = parse_query(url, slider_position=50, pattern_type='exclude', pattern='*.txt')
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["url"] == url
        assert result["pattern_type"] == "exclude"
        assert "*.txt" in result["ignore_patterns"]

def test_parse_query_include_pattern():
    url = "https://github.com/user/repo"
    result = parse_query(url, slider_position=50, pattern_type='include', pattern='*.py')
    assert result["pattern_type"] == "include"
    assert result["include_patterns"] == ["*.py"]
    assert result["ignore_patterns"] == DEFAULT_IGNORE_PATTERNS

def test_parse_query_invalid_pattern():
    url = "https://github.com/user/repo"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        parse_query(url, slider_position=50, pattern_type='include', pattern='*.py;rm -rf')