import asyncio

from gitingest.query_parser import ParsedQuery


async def ingest_pull_request(
    query: ParsedQuery,
) -> tuple[str, str, str]:
    """
    Ingest a pull request and return its summary, directory structure, and file contents.
    """
    summary = f"Pull request {query.pull_or_issue_number} from {query.url}"
    diff_url = await _pull_request_url_to_diff_url(query)
    files_changed, diff_content = await _ingest_diff_url(diff_url)
    return summary, files_changed, diff_content


async def _ingest_diff_url(diff_url: str) -> tuple[str, str]:
    """
    Ingest a diff URL and return its summary, files changed, and diff content.
    """
    proc = await asyncio.create_subprocess_exec(
        "curl",
        diff_url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Failed to fetch diff content from {diff_url}")

    diff_content = stdout.decode()

    files_changed = _summarize_files_changed_from_diff_content(diff_content)
    return files_changed, diff_content


def _summarize_files_changed_from_diff_content(diff_content: str) -> str:
    """
    Summarize the files changed from a diff content.

    Given a diff content, return a summary of the files changed in the following format:
    ```
    path/to/file1.py (modified, +X/-Y)
    path/to/file2.py (added)
    path/to/file3.py (deleted)
    path/to/file4.py (renamed from path/to/file5.py)
    ```
    """
    raise NotImplementedError


async def _pull_request_url_to_diff_url(query: ParsedQuery) -> str:
    """Convert a pull request URL to a diff URL.

    The following providers are supported:

    - GitHub:
        <- https://github.com/cyclotruc/gitingest/pull/153
        -> https://github.com/cyclotruc/gitingest/pull/153.diff
    - Bitbucket:
        <- https://bitbucket.org//cyclotruc/gitingest/pullrequests/153
        -> https://api.bitbucket.org/2.0/repositories/cyclotruc/gitingest/pullrequests/153/diff
    - GitLab:
        <- https://gitlab.com/ruancomelli/testing-project/-/merge_requests/1
        -> https://gitlab.com/ruancomelli/testing-project/-/merge_requests/1.diff
    - Codeberg:
        <- https://codeberg.org/mergiraf/mergiraf/pulls/184
        -> https://codeberg.org/mergiraf/mergiraf/pulls/184.diff
    - Gitea:
        <- https://gitea.com/gitea/git/pulls/152
        -> https://gitea.com/gitea/git/pulls/152.diff
    - ... and any other provider in which diff URLs are of the form `<pr_url> + ".diff"`

    Note that Bitbucket URLs cannot be converted to diff URLs by simply appending `.diff` to the URL.
    Instead, the Bitbucket API must be used.

    Args:
        url: The URL of the pull request.

    Returns:
        The URL of the diff.
    """
    if query.host == "bitbucket.org":
        return _bitbucket_pr_url_to_diff_url(query)
    else:
        return f"{query.url}.diff"


def _bitbucket_pr_url_to_diff_url(query: ParsedQuery) -> str:
    """Convert a Bitbucket pull request URL to a diff URL.

    Args:
        url: The URL of the pull request.

    Returns:
        The URL of the diff.
    """
    return f"https://api.bitbucket.org/2.0/repositories/{query.user_name}/{query.repo_name}/pullrequests/{query.pull_or_issue_number}/diff"
