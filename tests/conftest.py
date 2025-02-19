"""
Fixtures for tests.

This file provides shared fixtures for creating sample queries, a temporary directory structure, and a helper function
to write `.ipynb` notebooks for testing notebook utilities.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict

import pytest

from gitingest.query_parsing import ParsedQuery

WriteNotebookFunc = Callable[[str, Dict[str, Any]], Path]


@pytest.fixture
def sample_query() -> ParsedQuery:
    """
    Provide a default `ParsedQuery` object for use in tests.

    This fixture returns a `ParsedQuery` pre-populated with typical fields and some default ignore patterns.

    Returns
    -------
    ParsedQuery
        The sample `ParsedQuery` object.
    """
    return ParsedQuery(
        user_name="test_user",
        repo_name="test_repo",
        url=None,
        subpath="/",
        local_path=Path("/tmp/test_repo").resolve(),
        slug="test_user/test_repo",
        id="id",
        branch="main",
        max_file_size=1_000_000,
        ignore_patterns={"*.pyc", "__pycache__", ".git"},
        include_patterns=None,
        pattern_type="exclude",
    )


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """
    Create a temporary directory structure for testing repository scanning.

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
        The temporary directory path provided by the `tmp_path` fixture.

    Returns
    -------
    Path
        The path to the created `test_repo` directory.
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
    """
    Provide a helper function to write a `.ipynb` notebook file with the given content.

    Parameters
    ----------
    tmp_path : Path
        The temporary directory path provided by the `tmp_path` fixture.

    Returns
    -------
    WriteNotebookFunc
        A callable that accepts a filename and a dictionary (representing JSON notebook data), writes it to a `.ipynb`
        file, and returns the path to the file.
    """

    def _write_notebook(name: str, content: Dict[str, Any]) -> Path:
        notebook_path = tmp_path / name
        with notebook_path.open(mode="w", encoding="utf-8") as f:
            json.dump(content, f)
        return notebook_path

    return _write_notebook
