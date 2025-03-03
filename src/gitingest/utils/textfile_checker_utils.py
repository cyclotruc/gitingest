""" Utility functions for checking whether a file is likely a text file or a binary file. """

from pathlib import Path

from gitingest.utils.ingestion_utils import _get_encoding_list


def is_textfile(path: Path) -> bool:
    """
    Determine whether a file is likely a text file or a binary file using various heuristics.

    Parameters
    ----------
    path : Path
        The path to the file to check.

    Returns
    -------
    bool
        True if the file is likely textual; False if it appears to be binary.
    """
    # Attempt to read a small portion (up to 1024 bytes) of the file in binary mode.
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
    except OSError:
        # If we cannot read the file for any reason, treat it as non-textual.
        return False

    # If the file is empty, we treat it as text.
    if not chunk:
        return True

    # Look for obvious binary indicators such as null (0x00) or 0xFF bytes.
    if b"\x00" in chunk or b"\xff" in chunk:
        return False

    for encoding in _get_encoding_list():
        try:
            with path.open(encoding=encoding) as f:
                f.read()
                return True
        except UnicodeDecodeError:
            continue
        except OSError:
            return False

    return False
