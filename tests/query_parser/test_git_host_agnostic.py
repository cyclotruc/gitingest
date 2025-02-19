"""
Tests to verify that the query parser is Git host agnostic.

These tests confirm that `parse_query` correctly identifies user/repo pairs and canonical URLs for GitHub, GitLab,
Bitbucket, Gitea, and Codeberg, even if the host is omitted.
"""

from typing import List

import pytest

from gitingest.query_parsing import parse_query


@pytest.mark.parametrize(
    "urls, expected_user, expected_repo, expected_url",
    [
        (
            [
                "https://github.com/tiangolo/fastapi",
                "github.com/tiangolo/fastapi",
                "tiangolo/fastapi",
            ],
            "tiangolo",
            "fastapi",
            "https://github.com/tiangolo/fastapi",
        ),
        (
            [
                "https://gitlab.com/gitlab-org/gitlab-runner",
                "gitlab.com/gitlab-org/gitlab-runner",
                "gitlab-org/gitlab-runner",
            ],
            "gitlab-org",
            "gitlab-runner",
            "https://gitlab.com/gitlab-org/gitlab-runner",
        ),
        (
            [
                "https://bitbucket.org/na-dna/llm-knowledge-share",
                "bitbucket.org/na-dna/llm-knowledge-share",
                "na-dna/llm-knowledge-share",
            ],
            "na-dna",
            "llm-knowledge-share",
            "https://bitbucket.org/na-dna/llm-knowledge-share",
        ),
        (
            [
                "https://gitea.com/xorm/xorm",
                "gitea.com/xorm/xorm",
                "xorm/xorm",
            ],
            "xorm",
            "xorm",
            "https://gitea.com/xorm/xorm",
        ),
        (
            [
                "https://codeberg.org/forgejo/forgejo",
                "codeberg.org/forgejo/forgejo",
                "forgejo/forgejo",
            ],
            "forgejo",
            "forgejo",
            "https://codeberg.org/forgejo/forgejo",
        ),
    ],
)
@pytest.mark.asyncio
async def test_parse_query_without_host(
    urls: List[str],
    expected_user: str,
    expected_repo: str,
    expected_url: str,
) -> None:
    """
    Test `parse_query` for Git host agnosticism.

    Given multiple URL variations for the same user/repo on different Git hosts (with or without host names):
    When `parse_query` is called with each variation,
    Then the parser should correctly identify the user, repo, canonical URL, and other default fields.
    """
    for url in urls:
        parsed_query = await parse_query(url, max_file_size=50, from_web=True)

        assert parsed_query.user_name == expected_user
        assert parsed_query.repo_name == expected_repo
        assert parsed_query.url == expected_url
        assert parsed_query.slug == f"{expected_user}-{expected_repo}"
        assert parsed_query.id is not None
        assert parsed_query.subpath == "/"
        assert parsed_query.branch is None
        assert parsed_query.commit is None
        assert parsed_query.type is None
