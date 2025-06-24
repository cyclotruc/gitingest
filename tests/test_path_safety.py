from gitingest.security.path_safety import is_safe_path


def test_path_traversal(tmp_path):
    bad = tmp_path / ".." / "evil.txt"
    assert not is_safe_path(tmp_path, bad)
