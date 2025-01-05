""" This module contains fixtures for the tests. """

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_query() -> dict[str, Any]:
    return {
        "user_name": "test_user",
        "repo_name": "test_repo",
        "local_path": "/tmp/test_repo",
        "subpath": "/",
        "branch": "main",
        "commit": None,
        "max_file_size": 1_000_000,
        "slug": "test_user/test_repo",
        "ignore_patterns": ["*.pyc", "__pycache__", ".git"],
        "include_patterns": None,
        "pattern_type": "exclude",
    }


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    # Creates the following structure:
    # test_repo/
    # ├── file1.txt
    # ├── file2.py
    # └── src/
    # |   ├── subfile1.txt
    # |   └── subfile2.py
    # |   └── subdir/
    # |       └── file_subdir.txt
    # |       └── file_subdir.py
    # └── dir1/
    # |   └── file_dir1.txt
    # └── dir2/
    #     └── file_dir2.txt

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
