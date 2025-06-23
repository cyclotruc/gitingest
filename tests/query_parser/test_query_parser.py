"""
Tests for the `query_parsing` module.

These tests cover URL parsing, pattern parsing, and handling of branches/subpaths for HTTP(S) repositories and local
paths.
"""

from pathlib import Path
from typing import Callable, List, Optional
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from gitingest.query_parsing import _parse_patterns, _parse_remote_repo, parse_query
from gitingest.schemas.ingestion_schema import IngestionQuery
from gitingest.utils.ignore_patterns import DEFAULT_IGNORE_PATTERNS
from tests.conftest import DEMO_URL

URLS_HTTPS: List[str] = [
    DEMO_URL,
    "https://gitlab.com/user/repo",
    "https://bitbucket.org/user/repo",
    "https://gitea.com/user/repo",
    "https://codeberg.org/user/repo",
    "https://gist.github.com/user/repo",
]

URLS_HTTP: List[str] = [url.replace("https://", "http://") for url in URLS_HTTPS]


@pytest.mark.parametrize("url", URLS_HTTPS, ids=lambda u: u)
@pytest.mark.asyncio
async def test_parse_url_valid_https(url: str) -> None:
    """Valid HTTPS URLs parse correctly and `query.url` equals the input."""
    query = await _assert_basic_repo_fields(url)

    assert query.url == url  # HTTPS: canonical URL should equal input


@pytest.mark.parametrize("url", URLS_HTTP, ids=lambda u: u)
@pytest.mark.asyncio
async def test_parse_url_valid_http(url: str) -> None:
    """Valid HTTP URLs parse correctly (slug check only)."""
    await _assert_basic_repo_fields(url)


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
@pytest.mark.parametrize("url", [DEMO_URL, "https://gitlab.com/user/repo"])
async def test_parse_query_basic(url: str) -> None:
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
    query = await parse_query(DEMO_URL, max_file_size=50, from_web=True, include_patterns="*.py")

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
    with pytest.raises(ValueError, match="Pattern.*contains invalid characters"):
        await parse_query(DEMO_URL, max_file_size=50, from_web=True, include_patterns="*.py;rm -rf")


@pytest.mark.asyncio
async def test_parse_url_with_subpaths(stub_branches: Callable[[List[str]], None]) -> None:
    """
    Test `_parse_remote_repo` with a URL containing branch and subpath.

    Given a URL referencing a branch ("main") and a subdir ("subdir/file"):
    When `_parse_remote_repo` is called with remote branch fetching,
    Then user, repo, branch, and subpath should be identified correctly.
    """
    url = DEMO_URL + "/tree/main/subdir/file"

    stub_branches(["main", "dev", "feature-branch"])

    query = await _assert_basic_repo_fields(url)

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
    query = await parse_query(DEMO_URL, max_file_size=10**9, from_web=True)

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
    query = await parse_query(DEMO_URL, max_file_size=50, from_web=True, include_patterns="", ignore_patterns="")

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
    query = await parse_query(
        DEMO_URL,
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
    url = ""

    with pytest.raises(ValueError, match="Invalid repository URL"):
        await parse_query(url, max_file_size=100, from_web=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path, expected_branch, expected_commit",
    [
        ("/tree/main", "main", None),
        ("/tree/abcd1234abcd1234abcd1234abcd1234abcd1234", None, "abcd1234abcd1234abcd1234abcd1234abcd1234"),
    ],
)
async def test_parse_url_branch_and_commit_distinction(
    path: str,
    expected_branch: str,
    expected_commit: str,
    stub_branches: Callable[[List[str]], None],
) -> None:
    """
    Test `_parse_remote_repo` distinguishing branch vs. commit hash.

    Given either a branch URL (e.g., ".../tree/main") or a 40-character commit URL:
    When `_parse_remote_repo` is called with branch fetching,
    Then the function should correctly set `branch` or `commit` based on the URL content.
    """
    stub_branches(["main", "dev", "feature-branch"])

    url = DEMO_URL + path
    query = await _assert_basic_repo_fields(url)

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
    url = DEMO_URL + "?arg=value#fragment"
    query = await _parse_remote_repo(url)

    assert query.user_name == "user"
    assert query.repo_name == "repo"
    assert query.url == DEMO_URL  # URL should be cleaned


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
    "path, expected_branch, expected_subpath",
    [
        ("/tree/main/src", "main", "/src"),
        ("/tree/fix1", "fix1", "/"),
        ("/tree/nonexistent-branch/src", "nonexistent-branch", "/src"),
    ],
)
async def test_parse_repo_source_with_failed_git_command(
    path: str,
    expected_branch: str,
    expected_subpath: str,
    mocker: MockerFixture,
) -> None:
    """
    Test `_parse_remote_repo` when git fetch fails.

    Given a URL referencing a branch, but Git fetching fails:
    When `_parse_remote_repo` is called,
    Then it should fall back to path components for branch identification.
    """
    url = DEMO_URL + path

    mock_fetch_branches = mocker.patch("gitingest.utils.git_utils.fetch_remote_branch_list", new_callable=AsyncMock)
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
    ("path", "expected_branch", "expected_subpath"),
    [
        ("/tree/feature/fix1/src", "feature/fix1", "/src"),
        ("/tree/main/src", "main", "/src"),
        ("", None, "/"),
        ("/tree/nonexistent-branch/src", None, "/"),
        ("/tree/fix", "fix", "/"),
        ("/blob/fix/page.html", "fix", "/page.html"),
    ],
)
async def test_parse_repo_source_with_various_url_patterns(
    path: str,
    expected_branch: Optional[str],
    expected_subpath: str,
    stub_branches: Callable[[List[str]], None],
) -> None:
    """
    `_parse_remote_repo` should detect (or reject) a branch and resolve the
    sub-path for various GitHub-style URL permutations.

    Branch discovery is stubbed so that only names passed to `stub_branches` are considered "remote".
    """
    stub_branches(["feature/fix1", "main", "feature-branch", "fix"])

    url = DEMO_URL + path
    query = await _assert_basic_repo_fields(url)

    assert query.branch == expected_branch
    assert query.subpath == expected_subpath


async def _assert_basic_repo_fields(url: str) -> IngestionQuery:
    """Run _parse_remote_repo and assert user, repo and slug are parsed."""

    query = await _parse_remote_repo(url)

    assert query.user_name == "user"
    assert query.repo_name == "repo"
    assert query.slug == "user-repo"

    return query
