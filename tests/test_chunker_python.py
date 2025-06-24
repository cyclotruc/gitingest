from pathlib import Path

from gitingest.chunking import chunk_file


def test_python_chunker(tmp_path: Path):
    sample = tmp_path / "simple.py"
    sample.write_text(
        "def foo():\n    return 1\n\nclass Bar:\n    def baz(self):\n        pass\n"
    )
    chunks = chunk_file(sample)
    assert any(c.kind == "function" for c in chunks)
    assert chunks[0].text.strip().startswith("def")
