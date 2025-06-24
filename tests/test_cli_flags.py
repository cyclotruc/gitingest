import subprocess, json, gzip, sys, os
from pathlib import Path
from gitingest.cli import main as cli_main


def test_cli_parallel(tmp_path, monkeypatch):
    sample = tmp_path / "file.py"
    sample.write_text("def f(): pass")
    out = tmp_path / "out.md"
    sys.argv = ["gitingest", str(sample), str(out), "--parallel"]
    cli_main(standalone_mode=False)
    assert out.exists()


def test_cli_compress(tmp_path, monkeypatch):
    sample = tmp_path / "file.py"
    sample.write_text("def f(): pass")
    out = tmp_path / "out.txt"
    sys.argv = ["gitingest", str(sample), str(out), "--compress"]
    cli_main(standalone_mode=False)
    assert Path(str(out) + ".gz").exists()
