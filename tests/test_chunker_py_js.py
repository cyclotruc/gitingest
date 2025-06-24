from pathlib import Path
from gitingest.chunking import chunk_file


def test_python_chunks(tmp_path):
    py = tmp_path / "a.py"
    py.write_text("def f(): pass\n\ndef g(): pass\n")
    chunks = chunk_file(py)
    kinds = {c.kind for c in chunks}
    assert "function" in kinds
    assert len(chunks) == 2


def test_js_chunks(tmp_path):
    js = tmp_path / "b.js"
    js.write_text("function hello(){}\nfunction bye(){}")
    chunks = chunk_file(js)
    assert len(chunks) == 2
