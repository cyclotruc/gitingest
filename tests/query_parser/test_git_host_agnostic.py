""" Tests to verify that the query parser is Git host agnostic. """

import pytest

from gitingest.query_parser import parse_query


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
    urls: list[str],
    expected_user: str,
    expected_repo: str,
    expected_url: str,
) -> None:
    for url in urls:
        result = await parse_query(url, max_file_size=50, from_web=True)
        # Common assertions for all cases
        assert result["user_name"] == expected_user
        assert result["repo_name"] == expected_repo
        assert result["url"] == expected_url
        assert result["slug"] == f"{expected_user}-{expected_repo}"
        assert result["id"] is not None
        assert result["subpath"] == "/"
        assert result["branch"] is None
        assert result["commit"] is None
        assert result["type"] is None
