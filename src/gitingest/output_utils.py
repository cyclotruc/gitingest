"""Utility helpers for writing digests."""

import gzip
from pathlib import Path


def write_digest(text: str, path: Path, compress: bool = False) -> None:
    """Write a digest to ``path``; gzip if ``compress`` is True.

    Parameters
    ----------
    text : str
        Digest text to write.
    path : Path
        Destination path.
    compress : bool, optional
        If ``True``, write gzip-compressed output.
    """
    if compress:
        with gzip.open(path.with_suffix(".gz"), "wt", compresslevel=9) as f:
            f.write(text)
    else:
        path.write_text(text)

def write_digest(text: str, path: Path, compress: bool = False) -> None:
    """Write text to a path optionally gzipped."""
    if compress:
        gz_path = path.with_suffix(".gz")
        with gzip.open(gz_path, "wt", encoding="utf-8") as f:
            f.write(text)
    else:
        path.write_text(text, encoding="utf-8")