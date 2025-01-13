""" Tests for the query_ingestion module """

from pathlib import Path
from typing import Any
from unittest.mock import patch

from gitingest.query_ingestion import _extract_files_content, _read_file_content, _scan_directory


def test_scan_directory(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    sample_query["local_path"] = temp_directory
    result = _scan_directory(temp_directory, query=sample_query)
    if result is None:
        assert False, "Result is None"

    assert result["type"] == "directory"
    assert result["file_count"] == 8  # All .txt and .py files
    assert result["dir_count"] == 4  # src, src/subdir, dir1, dir2
    assert len(result["children"]) == 5  # file1.txt, file2.py, src, dir1, dir2


def test_extract_files_content(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    sample_query["local_path"] = temp_directory
    nodes = _scan_directory(temp_directory, query=sample_query)
    if nodes is None:
        assert False, "Nodes is None"
    files = _extract_files_content(query=sample_query, node=nodes, max_file_size=1_000_000)
    assert len(files) == 8  # All .txt and .py files

    # Check for presence of key files
    paths = [f["path"] for f in files]
    assert any("file1.txt" in p for p in paths)
    assert any("subfile1.txt" in p for p in paths)
    assert any("file2.py" in p for p in paths)
    assert any("subfile2.py" in p for p in paths)
    assert any("file_subdir.txt" in p for p in paths)
    assert any("file_dir1.txt" in p for p in paths)
    assert any("file_dir2.txt" in p for p in paths)


def test_read_file_content_with_notebook(tmp_path: Path):
    notebook_path = tmp_path / "dummy_notebook.ipynb"
    notebook_path.write_text("{}", encoding="utf-8")  # minimal JSON

    # Patch the symbol as it is used in query_ingestion
    with patch("gitingest.query_ingestion.process_notebook") as mock_process:
        _read_file_content(notebook_path)
        mock_process.assert_called_once_with(notebook_path)


def test_read_file_content_with_non_notebook(tmp_path: Path):
    py_file_path = tmp_path / "dummy_file.py"
    py_file_path.write_text("print('Hello')", encoding="utf-8")

    with patch("gitingest.query_ingestion.process_notebook") as mock_process:
        _read_file_content(py_file_path)
        mock_process.assert_not_called()


# Test that when using a ['*.txt'] as include pattern, only .txt files are processed & .py files are excluded
def test_include_txt_pattern(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    sample_query["local_path"] = temp_directory
    sample_query["include_patterns"] = ["*.txt"]

    result = _scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Result should not be None"

    files = _extract_files_content(query=sample_query, node=result, max_file_size=1_000_000)
    file_paths = [f["path"] for f in files]
    assert len(files) == 5, "Should have found exactly 5 .txt files"
    assert all(path.endswith(".txt") for path in file_paths), "Should only include .txt files"

    expected_files = ["file1.txt", "subfile1.txt", "file_subdir.txt", "file_dir1.txt", "file_dir2.txt"]
    for expected_file in expected_files:
        assert any(expected_file in path for path in file_paths), f"Missing expected file: {expected_file}"

    assert not any(path.endswith(".py") for path in file_paths), "Should not include .py files"


def test_include_nonexistent_extension(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    sample_query["local_path"] = temp_directory
    sample_query["include_patterns"] = ["*.query"]  # Is a Non existant extension ?

    result = _scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Result should not be None"

    # Extract the files content & set file limit cap
    files = _extract_files_content(query=sample_query, node=result, max_file_size=1_000_000)
    # Verify no file processed with wrong extension
    assert len(files) == 0, "Should not find any files with .qwerty extension"

    assert result["type"] == "directory"
    assert result["file_count"] == 0
    assert result["dir_count"] == 0
    assert len(result["children"]) == 0


# single folder patterns
def test_include_src_star_pattern(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    """
    Test that when using 'src/*' as include pattern, files under the src directory
    are included.
    Note: Windows is not supported - test converts Windows paths to Unix-style for validation.
    """
    sample_query["local_path"] = temp_directory
    sample_query["include_patterns"] = ["src/*"]

    result = _scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Result should not be None"

    files = _extract_files_content(query=sample_query, node=result, max_file_size=1_000_000)
    # Convert Windows paths to Unix-style for test validation
    file_paths = {f["path"].replace("\\", "/") for f in files}
    expected_paths = {"src/subfile1.txt", "src/subfile2.py", "src/subdir/file_subdir.txt", "src/subdir/file_subdir.py"}
    assert file_paths == expected_paths, "Missing or unexpected files in result"


def test_include_src_recursive(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    """
    Test that when using 'src/**' as include pattern, all files under src
    directory are included recursively.
    Note: Windows is not supported - test converts Windows paths to Unix-style for validation.
    """
    sample_query["local_path"] = temp_directory
    sample_query["include_patterns"] = ["src/**"]

    result = _scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Result should not be None"

    files = _extract_files_content(query=sample_query, node=result, max_file_size=1_000_000)
    # Convert Windows paths to Unix-style for test validation
    file_paths = {f["path"].replace("\\", "/") for f in files}
    expected_paths = {"src/subfile1.txt", "src/subfile2.py", "src/subdir/file_subdir.txt", "src/subdir/file_subdir.py"}
    assert file_paths == expected_paths, "Missing or unexpected files in result"


def test_include_src_wildcard_prefix(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    """
    Test that when using 'src*' as include pattern, it matches the src directory
    and any paths that start with 'src'.
    Note: Windows is not supported - test converts Windows paths to Unix-style for validation.
    """
    sample_query["local_path"] = temp_directory
    sample_query["include_patterns"] = ["src*"]

    result = _scan_directory(temp_directory, query=sample_query)
    assert result is not None, "Result should not be None"

    files = _extract_files_content(query=sample_query, node=result, max_file_size=1_000_000)
    # Convert Windows paths to Unix-style for test validation
    file_paths = {f["path"].replace("\\", "/") for f in files}
    expected_paths = {"src/subfile1.txt", "src/subfile2.py", "src/subdir/file_subdir.txt", "src/subdir/file_subdir.py"}
    assert file_paths == expected_paths, "Missing or unexpected files in result"


# multiple patterns
# TODO: test with multiple include patterns: ['*.txt', '*.py']
# TODO: test with multiple include patterns: ['/src/*', '*.txt']
# TODO: test with multiple include patterns: ['/src*', '*.txt']
