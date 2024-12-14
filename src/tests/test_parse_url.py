import pytest
from utils.parse_url import parse_url

def test_parse_url_valid():
    url = "https://github.com/user/repo"
    max_file_size = 100
    result = parse_url(url, max_file_size)
    assert result["user_name"] == "user"
    assert result["repo_name"] == "repo"
    assert result["url"] == "https://github.com/user/repo"
    assert result["max_file_size"] == 100 * 1024

def test_parse_url_invalid():
    url = "https://invalid.com/user/repo"
    max_file_size = 100
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        parse_url(url, max_file_size) 