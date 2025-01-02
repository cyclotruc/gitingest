import pytest

from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS
from gitingest.parse_query import _parse_patterns, _parse_url, parse_query


def test_parse_url_valid_https() -> None:
    test_cases = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo",
        "https://bitbucket.org/user/repo",
    ]
    for url in test_cases:
        result = _parse_url(url)
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["url"] == url


def test_parse_url_valid_http() -> None:
    test_cases = [
        "http://github.com/user/repo",
        "http://gitlab.com/user/repo",
        "http://bitbucket.org/user/repo",
    ]
    for url in test_cases:
        result = _parse_url(url)
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["slug"] == "user-repo"


def test_parse_url_invalid() -> None:
    url = "https://only-domain.com"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        _parse_url(url)


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


def test_parse_url_with_subpaths() -> None:
    url = "https://github.com/user/repo/tree/main/subdir/file"
    result = _parse_url(url)
    assert result["user_name"] == "user"
    assert result["repo_name"] == "repo"
    assert result["branch"] == "main"
    assert result["subpath"] == "/subdir/file"


def test_parse_url_invalid_repo_structure() -> None:
    url = "https://github.com/user"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        _parse_url(url)


def test_parse_patterns_valid() -> None:
    patterns = "*.py, *.md, docs/*"
    result = _parse_patterns(patterns)
    assert result == ["*.py", "*.md", "docs/*"]


def test_parse_patterns_invalid_characters() -> None:
    patterns = "*.py;rm -rf"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        _parse_patterns(patterns)


def test_parse_query_with_large_file_size() -> None:
    url = "https://github.com/user/repo"
    result = parse_query(url, max_file_size=10**9, from_web=True)
    assert result["max_file_size"] == 10**9
    assert result["ignore_patterns"] == DEFAULT_IGNORE_PATTERNS


def test_parse_query_empty_patterns() -> None:
    url = "https://github.com/user/repo"
    result = parse_query(url, max_file_size=50, from_web=True, include_patterns="", ignore_patterns="")
    assert result["include_patterns"] is None
    assert result["ignore_patterns"] == DEFAULT_IGNORE_PATTERNS


def test_parse_query_include_and_ignore_overlap() -> None:
    url = "https://github.com/user/repo"
    result = parse_query(
        url,
        max_file_size=50,
        from_web=True,
        include_patterns="*.py",
        ignore_patterns=["*.py", "*.txt"],
    )
    assert result["include_patterns"] == ["*.py"]
    assert "*.py" not in result["ignore_patterns"]
    assert "*.txt" in result["ignore_patterns"]


def test_parse_query_local_path() -> None:
    path = "/home/user/project"
    result = parse_query(path, max_file_size=100, from_web=False)
    assert result["local_path"] == "/home/user/project"
    assert result["id"] is not None
    assert result["slug"] == "user/project"


def test_parse_query_relative_path() -> None:
    path = "./project"
    result = parse_query(path, max_file_size=100, from_web=False)
    assert result["local_path"].endswith("project")
    assert result["slug"].endswith("project")


def test_parse_query_empty_source() -> None:
    with pytest.raises(ValueError, match="Invalid repository URL"):
        parse_query("", max_file_size=100, from_web=True)


def test_parse_url_branch_and_commit_distinction() -> None:
    url_branch = "https://github.com/user/repo/tree/main"
    url_commit = "https://github.com/user/repo/tree/abcd1234abcd1234abcd1234abcd1234abcd1234"

    result_branch = _parse_url(url_branch)
    result_commit = _parse_url(url_commit)

    assert result_branch["branch"] == "main"
    assert result_branch["commit"] is None

    assert result_commit["branch"] is None
    assert result_commit["commit"] == "abcd1234abcd1234abcd1234abcd1234abcd1234"


def test_parse_query_uuid_uniqueness() -> None:
    path = "/home/user/project"
    result1 = parse_query(path, max_file_size=100, from_web=False)
    result2 = parse_query(path, max_file_size=100, from_web=False)
    assert result1["id"] != result2["id"]
