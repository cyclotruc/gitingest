""" Utilities for processing Jupyter notebooks. """

import json
from pathlib import Path


def process_notebook(file: Path) -> str:
    """
    Process a Jupyter notebook file and return an executable Python script as a string.

    Parameters
    ----------
    file : Path
        The path to the Jupyter notebook file.

    Returns
    -------
    str
        The executable Python script as a string.

    Raises
    ------
    ValueError
        If an unexpected cell type is encountered.
    """
    with file.open(encoding="utf-8") as f:
        notebook = json.load(f)

    result = []

    for cell in notebook["cells"]:
        cell_type = cell.get("cell_type")

        # Validate cell type and handle unexpected types
        if cell_type not in ("markdown", "code", "raw"):
            raise ValueError(f"Unknown cell type: {cell_type}")

        str_ = "".join(cell.get("source", []))
        if not str_:
            continue

        # Convert Markdown and raw cells to multi-line comments
        if cell_type in ("markdown", "raw"):
            str_ = f'"""\n{str_}\n"""'

        result.append(str_)

    return "\n\n".join(result)
