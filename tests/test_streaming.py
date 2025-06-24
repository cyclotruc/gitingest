import asyncio
from pathlib import Path

import pytest

from gitingest.streaming import stream_remote_repo
from gitingest.entrypoint import ingest_async


def test_stream_remote_repo_downloads_files(tmp_path: Path) -> None:
    stream_remote_repo("https://github.com/octocat/Hello-World", branch="master", dest=tmp_path)
    assert (tmp_path / "README").exists()
    assert not (tmp_path / ".git").exists()


@pytest.mark.asyncio
async def test_ingest_async_stream(tmp_path: Path) -> None:
    summary, tree, content = await ingest_async(
        "https://github.com/octocat/Hello-World",
        branch="master",
        parallel=False,
        stream=True,
    )
    assert "README" in tree
    assert "Hello World!" in content
