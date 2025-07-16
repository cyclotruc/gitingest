"""Fixtures for tests.

This file provides shared fixtures for creating sample queries, a temporary directory structure, and a helper function
to write ``.ipynb`` notebooks for testing notebook utilities.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict
from unittest.mock import AsyncMock

import pytest

from gitingest.query_parser import IngestionQuery

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

WriteNotebookFunc = Callable[[str, Dict[str, Any]], Path]

DEMO_URL = "https://github.com/user/repo"
LOCAL_REPO_PATH = "/tmp/repo"
DEMO_COMMIT = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def get_ensure_git_installed_call_count() -> int:
    """Get the number of calls made by ensure_git_installed based on platform.

    On Windows, ensure_git_installed makes 2 calls:
    1. git --version
    2. git config core.longpaths

    On other platforms, it makes 1 call:
    1. git --version

    Returns
    -------
    int
        The number of calls made by ensure_git_installed

    """
    return 2 if sys.platform == "win32" else 1


@pytest.fixture
def sample_query() -> IngestionQuery:
    """Provide a default ``IngestionQuery`` object for use in tests.

    This fixture returns a ``IngestionQuery`` pre-populated with typical fields and some default ignore patterns.

    Returns
    -------
    IngestionQuery
        The sample ``IngestionQuery`` object.

    """
    return IngestionQuery(
        user_name="test_user",
        repo_name="test_repo",
        local_path=Path("/tmp/test_repo").resolve(),
        slug="test_user/test_repo",
        id="id",
        branch="main",
        max_file_size=1_000_000,
        ignore_patterns={"*.pyc", "__pycache__", ".git"},
    )


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Create a temporary directory structure for testing repository scanning.

    The structure includes:
    test_repo/
    ├── file1.txt
    ├── file2.py
    ├── src/
    │   ├── subfile1.txt
    │   ├── subfile2.py
    │   └── subdir/
    │       ├── file_subdir.txt
    │       └── file_subdir.py
    ├── dir1/
    │   └── file_dir1.txt
    └── dir2/
        └── file_dir2.txt

    Parameters
    ----------
    tmp_path : Path
        The temporary directory path provided by the ``tmp_path`` fixture.

    Returns
    -------
    Path
        The path to the created ``test_repo`` directory.

    """
    test_dir = tmp_path / "test_repo"
    test_dir.mkdir()

    # Root files
    (test_dir / "file1.txt").write_text("Hello World")
    (test_dir / "file2.py").write_text("print('Hello')")

    # src directory and its files
    src_dir = test_dir / "src"
    src_dir.mkdir()
    (src_dir / "subfile1.txt").write_text("Hello from src")
    (src_dir / "subfile2.py").write_text("print('Hello from src')")

    # src/subdir and its files
    subdir = src_dir / "subdir"
    subdir.mkdir()
    (subdir / "file_subdir.txt").write_text("Hello from subdir")
    (subdir / "file_subdir.py").write_text("print('Hello from subdir')")

    # dir1 and its file
    dir1 = test_dir / "dir1"
    dir1.mkdir()
    (dir1 / "file_dir1.txt").write_text("Hello from dir1")

    # dir2 and its file
    dir2 = test_dir / "dir2"
    dir2.mkdir()
    (dir2 / "file_dir2.txt").write_text("Hello from dir2")

    return test_dir


@pytest.fixture
def write_notebook(tmp_path: Path) -> WriteNotebookFunc:
    """Provide a helper function to write a ``.ipynb`` notebook file with the given content.

    Parameters
    ----------
    tmp_path : Path
        The temporary directory path provided by the ``tmp_path`` fixture.

    Returns
    -------
    WriteNotebookFunc
        A callable that accepts a filename and a dictionary (representing JSON notebook data), writes it to a
        ``.ipynb`` file, and returns the path to the file.

    """

    def _write_notebook(name: str, content: dict[str, Any]) -> Path:
        notebook_path = tmp_path / name
        with notebook_path.open(mode="w", encoding="utf-8") as f:
            json.dump(content, f)
        return notebook_path

    return _write_notebook


@pytest.fixture
def stub_branches(mocker: MockerFixture) -> Callable[[list[str]], None]:
    """Return a function that stubs git branch discovery to *branches*."""

    def _factory(branches: list[str]) -> None:
        mocker.patch(
            "gitingest.utils.git_utils.run_command",
            new_callable=AsyncMock,
            return_value=("\n".join(f"refs/heads/{b}" for b in branches).encode() + b"\n", b""),
        )
        mocker.patch(
            "gitingest.utils.git_utils.fetch_remote_branches_or_tags",
            new_callable=AsyncMock,
            return_value=branches,
        )

    return _factory


@pytest.fixture
def repo_exists_true(mocker: MockerFixture) -> AsyncMock:
    """Patch ``gitingest.clone.check_repo_exists`` to always return ``True``."""
    return mocker.patch("gitingest.clone.check_repo_exists", return_value=True)


@pytest.fixture
def run_command_mock(mocker: MockerFixture) -> AsyncMock:
    """Patch ``gitingest.clone.run_command`` with an ``AsyncMock``.

    The mocked function returns a dummy process whose ``communicate`` method yields generic
    ``stdout`` / ``stderr`` bytes. Tests can still access / tweak the mock via the fixture argument.
    """
    mock = AsyncMock(side_effect=_fake_run_command)
    mocker.patch("gitingest.utils.git_utils.run_command", mock)
    mocker.patch("gitingest.clone.run_command", mock)
    return mock


async def _fake_run_command(*args: str) -> tuple[bytes, bytes]:
    if "ls-remote" in args:
        # single match: <sha> <tab>refs/heads/main
        return (f"{DEMO_COMMIT}\trefs/heads/main\n".encode(), b"")
    return (b"output", b"error")
