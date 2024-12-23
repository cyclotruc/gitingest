import pytest
from src.gitingest.ingest_from_query import (
    scan_directory,
    extract_files_content,
    generate_suggestions,
    check_relevance,
    sort_suggestions
)

# Test fixtures
@pytest.fixture
def sample_query():
    return {
        'user_name': 'test_user',
        'repo_name': 'test_repo',
        'local_path': '/tmp/test_repo',
        'subpath': '/',
        'branch': 'main',
        'commit': None,
        'max_file_size': 1000000,
        'slug': 'test_user/test_repo',
        'ignore_patterns': ['*.pyc', '__pycache__', '.git'],
        'include_patterns': None,
        'pattern_type': 'exclude'
        
    }

@pytest.fixture
def temp_directory(tmp_path):
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

def test_scan_directory(temp_directory, sample_query):
    result = scan_directory(
        str(temp_directory),
        query=sample_query
    )
    
    assert result['type'] == 'directory'
    assert result['file_count'] == 8  # All .txt and .py files
    assert result['dir_count'] == 4   # src, src/subdir, dir1, dir2
    assert len(result['children']) == 5  # file1.txt, file2.py, src, dir1, dir2

def test_extract_files_content(temp_directory, sample_query):
    nodes = scan_directory(
        str(temp_directory),
        query=sample_query
    )
    
    files = extract_files_content(sample_query, nodes, max_file_size=1000000)
    assert len(files) == 8  # All .txt and .py files
    
    # Check for presence of key files
    paths = [f['path'] for f in files]
    assert any('file1.txt' in p for p in paths)
    assert any('subfile1.txt' in p for p in paths)
    assert any('file2.py' in p for p in paths)
    assert any('subfile2.py' in p for p in paths)
    assert any('file_subdir.txt' in p for p in paths)
    assert any('file_dir1.txt' in p for p in paths)
    assert any('file_dir2.txt' in p for p in paths)

def test_generate_suggestions(temp_directory, sample_query):
    sample_query['local_path'] = str(temp_directory)
    suggestions = generate_suggestions(sample_query)
    assert "*.md" in suggestions
    assert "*.py" in suggestions
    assert "*.json" in suggestions
    assert ".gitignore" in suggestions
    assert "*.docs" in suggestions
    assert "*.css" in suggestions
    assert "*.html" in suggestions
    assert "tests/*" in suggestions

def test_check_relevance(temp_directory, sample_query):
    sample_query['local_path'] = str(temp_directory)
    assert check_relevance(sample_query, "*.py") == True
    assert check_relevance(sample_query, "*.md") == False

def test_sort_suggestions(temp_directory, sample_query):
    sample_query['local_path'] = str(temp_directory)
    suggestions = generate_suggestions(sample_query)
    sorted_suggestions = sort_suggestions(sample_query, suggestions)
    assert sorted_suggestions[0] == "*.py"
    assert sorted_suggestions[1] == "*.md"
    assert sorted_suggestions[2] == "*.json"
    assert sorted_suggestions[3] == ".gitignore"
    assert sorted_suggestions[4] == "*.docs"
    assert sorted_suggestions[5] == "*.css"
    assert sorted_suggestions[6] == "*.html"
    assert sorted_suggestions[7] == "tests/*"

# TODO: test with include patterns: ['*.txt']
# TODO: test with wrong include patterns: ['*.qwerty']

#single folder patterns
# TODO: test with include patterns: ['src/*']
# TODO: test with include patterns: ['/src/*']
# TODO: test with include patterns: ['/src/']
# TODO: test with include patterns: ['/src*']

#multiple patterns
# TODO: test with multiple include patterns: ['*.txt', '*.py']
# TODO: test with multiple include patterns: ['/src/*', '*.txt']
# TODO: test with multiple include patterns: ['/src*', '*.txt']
