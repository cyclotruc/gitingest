"""
Tests for the `query_ingestion` module.

These tests validate directory scanning, file content extraction, notebook handling, and the overall ingestion logic,
including filtering patterns and subpaths.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from gitingest.ingestion import FileSystemNodeType, ingest_query, scan_directory
from gitingest.query_parsing import ParsedQuery


def test_scan_directory(temp_directory: Path, sample_query: ParsedQuery) -> None:
    """
    Test `scan_directory` with default settings.

    Given a populated test directory:
    When `scan_directory` is called,
    Then it should return a structured node containing the correct directories and file counts.
    """
    sample_query.local_path = temp_directory
    node = scan_directory(temp_directory, query=sample_query)

    assert node is not None, "Expected a valid directory node structure"
    assert node.type == FileSystemNodeType.DIRECTORY, "Root node should be a directory"
    assert node.file_count == 8, "Should count all .txt and .py files"
    assert node.dir_count == 4, "Should include src, src/subdir, dir1, dir2"
    assert len(node.children) == 5, "Should contain file1.txt, file2.py, src, dir1, dir2"


def test_extract_files_content(temp_directory: Path, sample_query: ParsedQuery) -> None:
    """
    Test `_extract_files_content` to ensure it gathers contents from scanned nodes.

    Given a populated test directory:
    When `_extract_files_content` is called with a valid scan result,
    Then it should return a list of file info containing the correct filenames and paths.
    """
    sample_query.local_path = temp_directory
    nodes = scan_directory(temp_directory, query=sample_query)

    assert nodes is not None, "Expected a valid scan result"

    file_nodes = _extract_files_content(query=sample_query, node=nodes, file_nodes=[])

    assert len(file_nodes) == 8, "Should extract all .txt and .py files"

    paths = [f.path for f in file_nodes]

    # Verify presence of key files
    assert any("file1.txt" in p for p in paths)
    assert any("subfile1.txt" in p for p in paths)
    assert any("file2.py" in p for p in paths)
    assert any("subfile2.py" in p for p in paths)
    assert any("file_subdir.txt" in p for p in paths)
    assert any("file_dir1.txt" in p for p in paths)
    assert any("file_dir2.txt" in p for p in paths)


def test_include_txt_pattern(temp_directory: Path, sample_query: ParsedQuery) -> None:
    """
    Test including only .txt files using a pattern like `*.txt`.

    Given a directory with mixed .txt and .py files:
    When `include_patterns` is set to `*.txt`,
    Then `scan_directory` should include only .txt files, excluding .py files.
    """
    sample_query.local_path = temp_directory
    sample_query.include_patterns = {"*.txt"}

    result = scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Expected a valid directory node structure"

    file_nodes = _extract_files_content(query=sample_query, node=result, file_nodes=[])
    file_paths = [f.path for f in file_nodes]

    assert len(file_nodes) == 5, "Should find exactly 5 .txt files"
    assert all(path.endswith(".txt") for path in file_paths), "Should only include .txt files"

    expected_files = ["file1.txt", "subfile1.txt", "file_subdir.txt", "file_dir1.txt", "file_dir2.txt"]
    for expected_file in expected_files:
        assert any(expected_file in path for path in file_paths), f"Missing expected file: {expected_file}"

    assert not any(path.endswith(".py") for path in file_paths), "No .py files should be included"


def test_include_nonexistent_extension(temp_directory: Path, sample_query: ParsedQuery) -> None:
    """
    Test including a nonexistent extension (e.g., `*.query`).

    Given a directory with no files matching `*.query`:
    When `scan_directory` is called with that pattern,
    Then no files should be returned in the result.
    """
    sample_query.local_path = temp_directory
    sample_query.include_patterns = {"*.query"}  # Nonexistent extension

    node = scan_directory(temp_directory, query=sample_query)
    assert node is not None, "Expected a valid directory node structure"

    file_nodes = _extract_files_content(query=sample_query, node=node, file_nodes=[])
    assert len(file_nodes) == 0, "Should not find any files matching *.query"

    assert node.type == FileSystemNodeType.DIRECTORY
    assert node.file_count == 0, "No files counted with this pattern"
    assert node.dir_count == 0
    assert len(node.children) == 0


@pytest.mark.parametrize("include_pattern", ["src/*", "src/**", "src*"])
def test_include_src_patterns(temp_directory: Path, sample_query: ParsedQuery, include_pattern: str) -> None:
    """
    Test including files under the `src` directory with various patterns.

    Given a directory containing `src` with subfiles:
    When `include_patterns` is set to `src/*`, `src/**`, or `src*`,
    Then `scan_directory` should include the correct files under `src`.

    Note: Windows is not supported; paths are converted to Unix-style for validation.
    """
    sample_query.local_path = temp_directory
    sample_query.include_patterns = {include_pattern}

    result = scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Expected a valid directory node structure"

    files = _extract_files_content(query=sample_query, node=result, file_nodes=[])

    # Convert Windows paths to Unix-style
    file_paths = {f.path.replace("\\", "/") for f in files}

    expected_paths = {
        "src/subfile1.txt",
        "src/subfile2.py",
        "src/subdir/file_subdir.txt",
        "src/subdir/file_subdir.py",
    }
    assert file_paths == expected_paths, "Missing or unexpected files in result"


def test_run_ingest_query(temp_directory: Path, sample_query: ParsedQuery) -> None:
    """
    Test `ingest_query` to ensure it processes the directory and returns expected results.

    Given a directory with .txt and .py files:
    When `ingest_query` is invoked,
    Then it should produce a summary string listing the files analyzed and a combined content string.
    """
    sample_query.local_path = temp_directory
    sample_query.subpath = "/"
    sample_query.type = None

    summary, _, content = ingest_query(sample_query)

    assert "Repository: test_user/test_repo" in summary
    assert "Files analyzed: 8" in summary

    # Check presence of key files in the content
    assert "src/subfile1.txt" in content
    assert "src/subfile2.py" in content
    assert "src/subdir/file_subdir.txt" in content
    assert "src/subdir/file_subdir.py" in content
    assert "file1.txt" in content
    assert "file2.py" in content
    assert "dir1/file_dir1.txt" in content
    assert "dir2/file_dir2.txt" in content


# TODO: Additional tests:
# - Multiple include patterns, e.g. ["*.txt", "*.py"] or ["/src/*", "*.txt"].
# - Edge cases with weird file names or deep subdirectory structures.
