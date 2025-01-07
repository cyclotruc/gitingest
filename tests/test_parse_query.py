""" Tests for the parse_query module. """

from pathlib import Path

import pytest

from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS
from gitingest.parse_query import _parse_patterns, _parse_url, parse_query


def test_parse_url_valid_https() -> None:
    """
    Test `_parse_url` with valid HTTPS URLs from supported platforms (GitHub, GitLab, Bitbucket).
    Verifies that user and repository names are correctly extracted.
    """
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
    """
    Test `_parse_url` with valid HTTP URLs from supported platforms.
    Verifies that user and repository names, as well as the slug, are correctly extracted.
    """
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
    """
    Test `_parse_url` with an invalid URL that does not include a repository structure.
    Verifies that a ValueError is raised with an appropriate error message.
    """
    url = "https://only-domain.com"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        _parse_url(url)


def test_parse_query_basic() -> None:
    """
    Test `parse_query` with basic inputs including valid repository URLs.
    Verifies that user and repository names, URL, and ignore patterns are correctly parsed.
    """
    test_cases = ["https://github.com/user/repo", "https://gitlab.com/user/repo"]
    for url in test_cases:
        result = parse_query(url, max_file_size=50, from_web=True, ignore_patterns="*.txt")
        assert result["user_name"] == "user"
        assert result["repo_name"] == "repo"
        assert result["url"] == url
        assert "*.txt" in result["ignore_patterns"]


def test_parse_query_include_pattern() -> None:
    """
    Test `parse_query` with an include pattern.
    Verifies that the include pattern is set correctly and default ignore patterns are applied.
    """
    url = "https://github.com/user/repo"
    result = parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py")
    assert result["include_patterns"] == ["*.py"]
    assert set(result["ignore_patterns"]) == set(DEFAULT_IGNORE_PATTERNS)


def test_parse_query_invalid_pattern() -> None:
    """
    Test `parse_query` with an invalid pattern containing special characters.
    Verifies that a ValueError is raised with an appropriate error message.
    """
    url = "https://github.com/user/repo"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py;rm -rf")


def test_parse_url_with_subpaths() -> None:
    """
    Test `_parse_url` with a URL containing a branch and subpath.
    Verifies that user name, repository name, branch, and subpath are correctly extracted.
    """
    url = "https://github.com/user/repo/tree/main/subdir/file"
    result = _parse_url(url)
    assert result["user_name"] == "user"
    assert result["repo_name"] == "repo"
    assert result["branch"] == "main"
    assert result["subpath"] == "/subdir/file"


def test_parse_url_invalid_repo_structure() -> None:
    """
    Test `_parse_url` with an invalid repository structure in the URL.
    Verifies that a ValueError is raised with an appropriate error message.
    """
    url = "https://github.com/user"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        _parse_url(url)


def test_parse_patterns_valid() -> None:
    """
    Test `_parse_patterns` with valid patterns separated by commas.
    Verifies that the patterns are correctly parsed into a list.
    """
    patterns = "*.py, *.md, docs/*"
    result = _parse_patterns(patterns)
    assert result == ["*.py", "*.md", "docs/*"]


def test_parse_patterns_invalid_characters() -> None:
    """
    Test `_parse_patterns` with invalid patterns containing special characters.
    Verifies that a ValueError is raised with an appropriate error message.
    """
    patterns = "*.py;rm -rf"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        _parse_patterns(patterns)


def test_parse_query_with_large_file_size() -> None:
    """
    Test `parse_query` with a very large file size limit.
    Verifies that the file size limit and default ignore patterns are set correctly.
    """
    url = "https://github.com/user/repo"
    result = parse_query(url, max_file_size=10**9, from_web=True)
    assert result["max_file_size"] == 10**9
    assert result["ignore_patterns"] == DEFAULT_IGNORE_PATTERNS


def test_parse_query_empty_patterns() -> None:
    """
    Test `parse_query` with empty include and ignore patterns.
    Verifies that the include patterns are set to None and default ignore patterns are applied.
    """
    url = "https://github.com/user/repo"
    result = parse_query(url, max_file_size=50, from_web=True, include_patterns="", ignore_patterns="")
    assert result["include_patterns"] is None
    assert result["ignore_patterns"] == DEFAULT_IGNORE_PATTERNS


def test_parse_query_include_and_ignore_overlap() -> None:
    """
    Test `parse_query` with overlapping include and ignore patterns.
    Verifies that overlapping patterns are removed from the ignore patterns.
    """
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
    """
    Test `parse_query` with a local file path.
    Verifies that the local path is set, a unique ID is generated, and the slug is correctly created.
    """
    path = "/home/user/project"
    result = parse_query(path, max_file_size=100, from_web=False)
    tail = Path("home/user/project")
    assert result["local_path"].parts[-len(tail.parts) :] == tail.parts
    assert result["id"] is not None
    assert result["slug"] == "user/project"


def test_parse_query_relative_path() -> None:
    """
    Test `parse_query` with a relative file path.
    Verifies that the local path and slug are correctly resolved.
    """
    path = "./project"
    result = parse_query(path, max_file_size=100, from_web=False)
    tail = Path("project")
    assert result["local_path"].parts[-len(tail.parts) :] == tail.parts
    assert result["slug"].endswith("project")


def test_parse_query_empty_source() -> None:
    """
    Test `parse_query` with an empty source input.
    Verifies that a ValueError is raised with an appropriate error message.
    """
    with pytest.raises(ValueError, match="Invalid repository URL"):
        parse_query("", max_file_size=100, from_web=True)


def test_parse_url_branch_and_commit_distinction() -> None:
    """
    Test `_parse_url` with URLs containing either a branch name or a commit hash.
    Verifies that the branch and commit are correctly distinguished.
    """
    url_branch = "https://github.com/user/repo/tree/main"
    url_commit = "https://github.com/user/repo/tree/abcd1234abcd1234abcd1234abcd1234abcd1234"

    result_branch = _parse_url(url_branch)
    result_commit = _parse_url(url_commit)

    assert result_branch["branch"] == "main"
    assert result_branch["commit"] is None

    assert result_commit["branch"] is None
    assert result_commit["commit"] == "abcd1234abcd1234abcd1234abcd1234abcd1234"


def test_parse_query_uuid_uniqueness() -> None:
    """
    Test `parse_query` to ensure that each call generates a unique UUID for the query result.
    """
    path = "/home/user/project"
    result1 = parse_query(path, max_file_size=100, from_web=False)
    result2 = parse_query(path, max_file_size=100, from_web=False)
    assert result1["id"] != result2["id"]


def test_parse_url_with_query_and_fragment() -> None:
    """
    Test `_parse_url` with a URL containing query parameters and a fragment.
    Verifies that the URL is cleaned and other fields are correctly extracted.
    """
    url = "https://github.com/user/repo?arg=value#fragment"
    result = _parse_url(url)
    assert result["user_name"] == "user"
    assert result["repo_name"] == "repo"
    assert result["url"] == "https://github.com/user/repo"  # URL should be cleaned
