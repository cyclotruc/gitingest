from gitingest.output_utils import write_digest
from pathlib import Path
import gzip


def test_gzip_out(tmp_path):
    d = "hello world"
    path = tmp_path / "digest.txt"
    write_digest(d, path, compress=True)
    gz = path.with_suffix(".gz")
    assert gz.exists()
    with gzip.open(gz, "rt") as f:
        assert f.read() == d
