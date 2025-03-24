"""
Tests for the `query_parsing` module.

These tests cover URL parsing, pattern parsing, and handling of branches/subpaths for HTTP(S) repositories and local
paths.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from gitingest.query_parsing import _parse_patterns, _parse_remote_repo, parse_query
from gitingest.utils.ignore_patterns import DEFAULT_IGNORE_PATTERNS


@pytest.mark.asyncio
async def test_parse_url_valid_https() -> None:
    """
    Test `_parse_remote_repo` with valid HTTPS URLs.

    Given various HTTPS URLs on supported platforms:
    When `_parse_remote_repo` is called,
    Then user name, repo name, and the URL should be extracted correctly.
    """
    test_cases = [
        "https://github.com/user/repo",
        "https://gitlab.com/user/repo",
        "https://bitbucket.org/user/repo",
        "https://gitea.com/user/repo",
        "https://codeberg.org/user/repo",
        "https://gist.github.com/user/repo",
    ]
    for url in test_cases:
        query = await _parse_remote_repo(url)

        assert query.user_name == "user"
        assert query.repo_name == "repo"
        assert query.url == url


@pytest.mark.asyncio
async def test_parse_url_valid_http() -> None:
    """
    Test `_parse_remote_repo` with valid HTTP URLs.

    Given various HTTP URLs on supported platforms:
    When `_parse_remote_repo` is called,
    Then user name, repo name, and the slug should be extracted correctly.
    """
    test_cases = [
        "http://github.com/user/repo",
        "http://gitlab.com/user/repo",
        "http://bitbucket.org/user/repo",
        "http://gitea.com/user/repo",
        "http://codeberg.org/user/repo",
        "http://gist.github.com/user/repo",
    ]
    for url in test_cases:
        query = await _parse_remote_repo(url)

        assert query.user_name == "user"
        assert query.repo_name == "repo"
        assert query.slug == "user-repo"


@pytest.mark.asyncio
async def test_parse_url_invalid() -> None:
    """
    Test `_parse_remote_repo` with an invalid URL.

    Given an HTTPS URL lacking a repository structure (e.g., "https://github.com"),
    When `_parse_remote_repo` is called,
    Then a ValueError should be raised indicating an invalid repository URL.
    """
    url = "https://github.com"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        await _parse_remote_repo(url)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["https://github.com/user/repo", "https://gitlab.com/user/repo"])
async def test_parse_query_basic(url):
    """
    Test `parse_query` with a basic valid repository URL.

    Given an HTTPS URL and ignore_patterns="*.txt":
    When `parse_query` is called,
    Then user/repo, URL, and ignore patterns should be parsed correctly.
    """
    query = await parse_query(source=url, max_file_size=50, from_web=True, ignore_patterns="*.txt")

    assert query.user_name == "user"
    assert query.repo_name == "repo"
    assert query.url == url
    assert query.ignore_patterns
    assert "*.txt" in query.ignore_patterns


@pytest.mark.asyncio
async def test_parse_query_mixed_case() -> None:
    """
    Test `parse_query` with mixed-case URLs.

    Given a URL with mixed-case parts (e.g. "Https://GitHub.COM/UsEr/rEpO"):
    When `parse_query` is called,
    Then the user and repo names should be normalized to lowercase.
    """
    url = "Https://GitHub.COM/UsEr/rEpO"
    query = await parse_query(url, max_file_size=50, from_web=True)

    assert query.user_name == "user"
    assert query.repo_name == "repo"


@pytest.mark.asyncio
async def test_parse_query_include_pattern() -> None:
    """
    Test `parse_query` with a specified include pattern.

    Given a URL and include_patterns="*.py":
    When `parse_query` is called,
    Then the include pattern should be set, and default ignore patterns remain applied.
    """
    url = "https://github.com/user/repo"
    query = await parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py")

    assert query.include_patterns == {"*.py"}
    assert query.ignore_patterns == DEFAULT_IGNORE_PATTERNS


@pytest.mark.asyncio
async def test_parse_query_invalid_pattern() -> None:
    """
    Test `parse_query` with an invalid pattern.

    Given an include pattern containing special characters (e.g., "*.py;rm -rf"):
    When `parse_query` is called,
    Then a ValueError should be raised indicating invalid characters.
    """
    url = "https://github.com/user/repo"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        await parse_query(url, max_file_size=50, from_web=True, include_patterns="*.py;rm -rf")


@pytest.mark.asyncio
async def test_parse_url_with_subpaths() -> None:
    """
    Test `_parse_remote_repo` with a URL containing branch and subpath.

    Given a URL referencing a branch ("main") and a subdir ("subdir/file"):
    When `_parse_remote_repo` is called with remote branch fetching,
    Then user, repo, branch, and subpath should be identified correctly.
    """
    url = "https://github.com/user/repo/tree/main/subdir/file"
    with patch("gitingest.utils.git_utils.run_command", new_callable=AsyncMock) as mock_run_command:
        mock_run_command.return_value = (b"refs/heads/main\nrefs/heads/dev\nrefs/heads/feature-branch\n", b"")
        with patch(
            "gitingest.utils.git_utils.fetch_remote_branch_list", new_callable=AsyncMock
        ) as mock_fetch_branches:
            mock_fetch_branches.return_value = ["main", "dev", "feature-branch"]
            query = await _parse_remote_repo(url)

            assert query.user_name == "user"
            assert query.repo_name == "repo"
            assert query.branch == "main"
            assert query.subpath == "/subdir/file"


@pytest.mark.asyncio
async def test_parse_url_invalid_repo_structure() -> None:
    """
    Test `_parse_remote_repo` with a URL missing a repository name.

    Given a URL like "https://github.com/user":
    When `_parse_remote_repo` is called,
    Then a ValueError should be raised indicating an invalid repository URL.
    """
    url = "https://github.com/user"
    with pytest.raises(ValueError, match="Invalid repository URL"):
        await _parse_remote_repo(url)


def test_parse_patterns_valid() -> None:
    """
    Test `_parse_patterns` with valid comma-separated patterns.

    Given patterns like "*.py, *.md, docs/*":
    When `_parse_patterns` is called,
    Then it should return a set of parsed strings.
    """
    patterns = "*.py, *.md, docs/*"
    parsed_patterns = _parse_patterns(patterns)

    assert parsed_patterns == {"*.py", "*.md", "docs/*"}


def test_parse_patterns_invalid_characters() -> None:
    """
    Test `_parse_patterns` with invalid characters.

    Given a pattern string containing special characters (e.g. "*.py;rm -rf"):
    When `_parse_patterns` is called,
    Then a ValueError should be raised indicating invalid pattern syntax.
    """
    patterns = "*.py;rm -rf"
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        _parse_patterns(patterns)


@pytest.mark.asyncio
async def test_parse_query_with_large_file_size() -> None:
    """
    Test `parse_query` with a very large file size limit.

    Given a URL and max_file_size=10**9:
    When `parse_query` is called,
    Then `max_file_size` should be set correctly and default ignore patterns remain unchanged.
    """
    url = "https://github.com/user/repo"
    query = await parse_query(url, max_file_size=10**9, from_web=True)

    assert query.max_file_size == 10**9
    assert query.ignore_patterns == DEFAULT_IGNORE_PATTERNS


@pytest.mark.asyncio
async def test_parse_query_empty_patterns() -> None:
    """
    Test `parse_query` with empty patterns.

    Given empty include_patterns and ignore_patterns:
    When `parse_query` is called,
    Then include_patterns becomes None and default ignore patterns apply.
    """
    url = "https://github.com/user/repo"
    query = await parse_query(url, max_file_size=50, from_web=True, include_patterns="", ignore_patterns="")

    assert query.include_patterns is None
    assert query.ignore_patterns == DEFAULT_IGNORE_PATTERNS


@pytest.mark.asyncio
async def test_parse_query_include_and_ignore_overlap() -> None:
    """
    Test `parse_query` with overlapping patterns.

    Given include="*.py" and ignore={"*.py", "*.txt"}:
    When `parse_query` is called,
    Then "*.py" should be removed from ignore patterns.
    """
    url = "https://github.com/user/repo"
    query = await parse_query(
        url,
        max_file_size=50,
        from_web=True,
        include_patterns="*.py",
        ignore_patterns={"*.py", "*.txt"},
    )

    assert query.include_patterns == {"*.py"}
    assert query.ignore_patterns is not None
    assert "*.py" not in query.ignore_patterns
    assert "*.txt" in query.ignore_patterns


@pytest.mark.asyncio
async def test_parse_query_local_path() -> None:
    """
    Test `parse_query` with a local file path.

    Given "/home/user/project" and from_web=False:
    When `parse_query` is called,
    Then the local path should be set, id generated, and slug formed accordingly.
    """
    path = "/home/user/project"
    query = await parse_query(path, max_file_size=100, from_web=False)
    tail = Path("home/user/project")

    assert query.local_path.parts[-len(tail.parts) :] == tail.parts
    assert query.id is not None
    assert query.slug == "home/user/project"


@pytest.mark.asyncio
async def test_parse_query_relative_path() -> None:
    """
    Test `parse_query` with a relative path.

    Given "./project" and from_web=False:
    When `parse_query` is called,
    Then local_path resolves relatively, and slug ends with "project".
    """
    path = "./project"
    query = await parse_query(path, max_file_size=100, from_web=False)
    tail = Path("project")

    assert query.local_path.parts[-len(tail.parts) :] == tail.parts
    assert query.slug.endswith("project")


@pytest.mark.asyncio
async def test_parse_query_empty_source() -> None:
    """
    Test `parse_query` with an empty string.

    Given an empty source string:
    When `parse_query` is called,
    Then a ValueError should be raised indicating an invalid repository URL.
    """
    with pytest.raises(ValueError, match="Invalid repository URL"):
        await parse_query("", max_file_size=100, from_web=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, expected_branch, expected_commit",
    [
        ("https://github.com/user/repo/tree/main", "main", None),
        (
            "https://github.com/user/repo/tree/abcd1234abcd1234abcd1234abcd1234abcd1234",
            None,
            "abcd1234abcd1234abcd1234abcd1234abcd1234",
        ),
    ],
)
async def test_parse_url_branch_and_commit_distinction(url: str, expected_branch: str, expected_commit: str) -> None:
    """
    Test `_parse_remote_repo` distinguishing branch vs. commit hash.

    Given either a branch URL (e.g., ".../tree/main") or a 40-character commit URL:
    When `_parse_remote_repo` is called with branch fetching,
    Then the function should correctly set `branch` or `commit` based on the URL content.
    """
    with patch("gitingest.utils.git_utils.run_command", new_callable=AsyncMock) as mock_run_command:
        # Mocking the return value to include 'main' and some additional branches
        mock_run_command.return_value = (b"refs/heads/main\nrefs/heads/dev\nrefs/heads/feature-branch\n", b"")
        with patch(
            "gitingest.utils.git_utils.fetch_remote_branch_list", new_callable=AsyncMock
        ) as mock_fetch_branches:
            mock_fetch_branches.return_value = ["main", "dev", "feature-branch"]

            query = await _parse_remote_repo(url)

            # Verify that `branch` and `commit` match our expectations
            assert query.branch == expected_branch
            assert query.commit == expected_commit


@pytest.mark.asyncio
async def test_parse_query_uuid_uniqueness() -> None:
    """
    Test `parse_query` for unique UUID generation.

    Given the same path twice:
    When `parse_query` is called repeatedly,
    Then each call should produce a different query id.
    """
    path = "/home/user/project"
    query_1 = await parse_query(path, max_file_size=100, from_web=False)
    query_2 = await parse_query(path, max_file_size=100, from_web=False)

    assert query_1.id != query_2.id


@pytest.mark.asyncio
async def test_parse_url_with_query_and_fragment() -> None:
    """
    Test `_parse_remote_repo` with query parameters and a fragment.

    Given a URL like "https://github.com/user/repo?arg=value#fragment":
    When `_parse_remote_repo` is called,
    Then those parts should be stripped, leaving a clean user/repo URL.
    """
    url = "https://github.com/user/repo?arg=value#fragment"
    query = await _parse_remote_repo(url)

    assert query.user_name == "user"
    assert query.repo_name == "repo"
    assert query.url == "https://github.com/user/repo"  # URL should be cleaned


@pytest.mark.asyncio
async def test_parse_url_unsupported_host() -> None:
    """
    Test `_parse_remote_repo` with an unsupported host.

    Given "https://only-domain.com":
    When `_parse_remote_repo` is called,
    Then a ValueError should be raised for the unknown domain.
    """
    url = "https://only-domain.com"
    with pytest.raises(ValueError, match="Unknown domain 'only-domain.com' in URL"):
        await _parse_remote_repo(url)


@pytest.mark.asyncio
async def test_parse_query_with_branch() -> None:
    """
    Test `parse_query` when a branch is specified in a blob path.

    Given "https://github.com/pandas-dev/pandas/blob/2.2.x/...":
    When `parse_query` is called,
    Then the branch should be identified, subpath set, and commit remain None.
    """
    url = "https://github.com/pandas-dev/pandas/blob/2.2.x/.github/ISSUE_TEMPLATE/documentation_improvement.yaml"
    query = await parse_query(url, max_file_size=10**9, from_web=True)

    assert query.user_name == "pandas-dev"
    assert query.repo_name == "pandas"
    assert query.url == "https://github.com/pandas-dev/pandas"
    assert query.slug == "pandas-dev-pandas"
    assert query.id is not None
    assert query.subpath == "/.github/ISSUE_TEMPLATE/documentation_improvement.yaml"
    assert query.branch == "2.2.x"
    assert query.commit is None
    assert query.type == "blob"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, expected_branch, expected_subpath",
    [
        ("https://github.com/user/repo/tree/main/src", "main", "/src"),
        ("https://github.com/user/repo/tree/fix1", "fix1", "/"),
        ("https://github.com/user/repo/tree/nonexistent-branch/src", "nonexistent-branch", "/src"),
    ],
)
async def test_parse_repo_source_with_failed_git_command(url, expected_branch, expected_subpath):
    """
    Test `_parse_remote_repo` when git fetch fails.

    Given a URL referencing a branch, but Git fetching fails:
    When `_parse_remote_repo` is called,
    Then it should fall back to path components for branch identification.
    """
    with patch("gitingest.utils.git_utils.fetch_remote_branch_list", new_callable=AsyncMock) as mock_fetch_branches:
        mock_fetch_branches.side_effect = Exception("Failed to fetch branch list")

        with pytest.warns(
            RuntimeWarning,
            match="Warning: Failed to fetch branch list: Command failed: "
            "git ls-remote --heads https://github.com/user/repo",
        ):

            query = await _parse_remote_repo(url)

            assert query.branch == expected_branch
            assert query.subpath == expected_subpath


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, expected_branch, expected_subpath",
    [
        ("https://github.com/user/repo/tree/feature/fix1/src", "feature/fix1", "/src"),
        ("https://github.com/user/repo/tree/main/src", "main", "/src"),
        ("https://github.com/user/repo", None, "/"),  # No
        ("https://github.com/user/repo/tree/nonexistent-branch/src", None, "/"),  # Non-existent branch
        ("https://github.com/user/repo/tree/fix", "fix", "/"),
        ("https://github.com/user/repo/blob/fix/page.html", "fix", "/page.html"),
    ],
)
async def test_parse_repo_source_with_various_url_patterns(url, expected_branch, expected_subpath):
    """
    Test `_parse_remote_repo` with various URL patterns.

    Given multiple branch/blob patterns (including nonexistent branches):
    When `_parse_remote_repo` is called with remote branch fetching,
    Then the correct branch/subpath should be set or None if unmatched.
    """
    with patch("gitingest.utils.git_utils.run_command", new_callable=AsyncMock) as mock_run_command:
        with patch(
            "gitingest.utils.git_utils.fetch_remote_branch_list", new_callable=AsyncMock
        ) as mock_fetch_branches:
            mock_run_command.return_value = (
                b"refs/heads/feature/fix1\nrefs/heads/main\nrefs/heads/feature-branch\nrefs/heads/fix\n",
                b"",
            )
            mock_fetch_branches.return_value = ["feature/fix1", "main", "feature-branch"]

            query = await _parse_remote_repo(url)

            assert query.branch == expected_branch
            assert query.subpath == expected_subpath
