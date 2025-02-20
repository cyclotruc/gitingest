""" Utility functions for checking whether a file is likely a text file or a binary file. """

from pathlib import Path

import chardet


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
    except (IOError, OSError):
        # If we cannot read the file for any reason, treat it as non-textual.
        return False

    # If the file is empty, we treat it as text.
    if not chunk:
        return True

    # Define which bytes are considered control characters (excluding tabs, newlines, carriage returns).
    control_chars = set(range(0, 32)) - {9, 10, 13}
    # Include DEL (0x7F) as a control character.
    control_chars.add(127)

    # Calculate the ratio of control characters relative to the size of the chunk.
    control_count = sum(byte in control_chars for byte in chunk)
    control_ratio = control_count / len(chunk)

    # Calculate the ratio of high-ASCII characters (byte values > 127).
    high_ascii_count = sum(byte > 127 for byte in chunk)
    high_ascii_ratio = high_ascii_count / len(chunk)

    # If the control character ratio is extremely high but high ASCII is low, it's likely a binary file.
    if control_ratio > 0.90 and high_ascii_ratio < 0.90:
        return False

    # Use chardet to attempt to detect encoding. This can catch many textual encodings if confidence is high.
    detection_result = chardet.detect(chunk)
    encoding = detection_result.get("encoding")
    confidence = detection_result.get("confidence", 0.0)

    # If chardet cannot detect an encoding at all, treat it as binary.
    if encoding is None:
        return False

    # If confidence is high and detected encoding isn't ASCII, try to decode the chunk as text.
    if confidence > 0.9 and encoding.lower() != "ascii":
        try:
            chunk.decode(encoding=encoding)
            return True
        except UnicodeDecodeError:
            # If decoding fails, it's likely binary.
            return False

    # Look for obvious binary indicators such as null (0x00) or 0xFF bytes.
    if b"\x00" in chunk or b"\xff" in chunk:
        return False

    # Combine control characters and high-ASCII checks for a final binary heuristic.
    # If we have a moderately high control character ratio plus some high ASCII, or
    # if we have a very high control character ratio in general, it's likely binary.
    is_likely_binary = (
        (control_ratio > 0.3 and high_ascii_ratio > 0.05)
        or (control_ratio > 0.8 and high_ascii_ratio < 0.8)
    )
    if is_likely_binary:
        return False

    # If we haven't returned False by now, it is probably safe to treat the file as text.
    return True
