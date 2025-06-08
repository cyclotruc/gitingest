from pathlib import Path
import gzip


def write_digest(text: str, path: Path, compress: bool = False) -> None:
    """Write text to a path optionally gzipped."""
    if compress:
        gz_path = path.with_suffix(".gz")
        with gzip.open(gz_path, "wt", encoding="utf-8") as f:
            f.write(text)
    else:
        path.write_text(text, encoding="utf-8")
