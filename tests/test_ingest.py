""" Tests for the ingest_from_query module """

from pathlib import Path
from typing import Any

from gitingest.ingest_from_query import _extract_files_content, _scan_directory


def test_scan_directory(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    result = _scan_directory(str(temp_directory), query=sample_query)
    if result is None:
        assert False, "Result is None"

    assert result["type"] == "directory"
    assert result["file_count"] == 8  # All .txt and .py files
    assert result["dir_count"] == 4  # src, src/subdir, dir1, dir2
    assert len(result["children"]) == 5  # file1.txt, file2.py, src, dir1, dir2


def test_extract_files_content(temp_directory: Path, sample_query: dict[str, Any]) -> None:
    nodes = _scan_directory(str(temp_directory), query=sample_query)
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


# TODO: test with include patterns: ['*.txt']
# TODO: test with wrong include patterns: ['*.qwerty']


# single folder patterns
# TODO: test with include patterns: ['src/*']
# TODO: test with include patterns: ['/src/*']
# TODO: test with include patterns: ['/src/']
# TODO: test with include patterns: ['/src*']

# multiple patterns
# TODO: test with multiple include patterns: ['*.txt', '*.py']
# TODO: test with multiple include patterns: ['/src/*', '*.txt']
# TODO: test with multiple include patterns: ['/src*', '*.txt']
