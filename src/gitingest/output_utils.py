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
