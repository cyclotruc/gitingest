""" Utilities for processing Jupyter notebooks. """

import json
import warnings
from pathlib import Path
from typing import Any


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
        notebook: dict[str, Any] = json.load(f)

    # Check if the notebook contains worksheets
    if worksheets := notebook.get("worksheets"):
        # https://github.com/ipython/ipython/wiki/IPEP-17:-Notebook-Format-4#remove-multiple-worksheets
        #   "The `worksheets` field is a list, but we have no UI to support multiple worksheets.
        #   Our design has since shifted to heading-cell based structure, so we never intend to
        #   support the multiple worksheet model. The worksheets list of lists shall be replaced
        #   with a single list, called `cells`."
        warnings.warn("Worksheets are deprecated as of IPEP-17.", DeprecationWarning)

        if len(worksheets) > 1:
            warnings.warn(
                "Multiple worksheets are not supported. Only the first worksheet will be processed.", UserWarning
            )

        notebook = worksheets[0]

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
