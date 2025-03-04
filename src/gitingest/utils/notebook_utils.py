""" Utilities for processing Jupyter notebooks. """

import json
import warnings
from itertools import chain
from pathlib import Path
from typing import Any, Dict, List, Optional

from gitingest.exceptions import InvalidNotebookError


def process_notebook(file: Path, include_output: bool = True) -> str:
    """
    Process a Jupyter notebook file and return an executable Python script as a string.

    Parameters
    ----------
    file : Path
        The path to the Jupyter notebook file.
    include_output : bool
        Whether to include cell outputs in the generated script, by default True.

    Returns
    -------
    str
        The executable Python script as a string.

    Raises
    ------
    InvalidNotebookError
        If the notebook file is invalid or cannot be processed.
    """
    try:
        with file.open(encoding="utf-8") as f:
            notebook: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as exc:
        raise InvalidNotebookError(f"Invalid JSON in notebook: {file}") from exc

    # Check if the notebook contains worksheets
    worksheets = notebook.get("worksheets")
    if worksheets:
        warnings.warn(
            "Worksheets are deprecated as of IPEP-17. Consider updating the notebook. "
            "(See: https://github.com/jupyter/nbformat and "
            "https://github.com/ipython/ipython/wiki/IPEP-17:-Notebook-Format-4#remove-multiple-worksheets "
            "for more information.)",
            DeprecationWarning,
        )

        if len(worksheets) > 1:
            warnings.warn("Multiple worksheets detected. Combining all worksheets into a single script.", UserWarning)

        cells = list(chain.from_iterable(ws["cells"] for ws in worksheets))

    else:
        cells = notebook["cells"]

    result = ["# Jupyter notebook converted to Python script."]

    for cell in cells:
        cell_str = _process_cell(cell, include_output=include_output)
        if cell_str:
            result.append(cell_str)

    return "\n\n".join(result) + "\n"


def _process_cell(cell: Dict[str, Any], include_output: bool) -> Optional[str]:
    """
    Process a Jupyter notebook cell and return the cell content as a string.

    Parameters
    ----------
    cell : Dict[str, Any]
        The cell dictionary from a Jupyter notebook.
    include_output : bool
        Whether to include cell outputs in the generated script

    Returns
    -------
    str, optional
        The cell content as a string, or None if the cell is empty.

    Raises
    ------
    ValueError
        If an unexpected cell type is encountered.
    """
    cell_type = cell["cell_type"]

    # Validate cell type and handle unexpected types
    if cell_type not in ("markdown", "code", "raw"):
        raise ValueError(f"Unknown cell type: {cell_type}")

    cell_str = "".join(cell["source"])

    # Skip empty cells
    if not cell_str:
        return None

    # Convert Markdown and raw cells to multi-line comments
    if cell_type in ("markdown", "raw"):
        return f'"""\n{cell_str}\n"""'

    # Add cell output as comments
    outputs = cell.get("outputs")
    if include_output and outputs:

        # Include cell outputs as comments
        output_lines = []

        for output in outputs:
            output_lines += _extract_output(output)

        for output_line in output_lines:
            if not output_line.endswith("\n"):
                output_line += "\n"

        cell_str += "\n# Output:\n#   " + "\n#   ".join(output_lines)

    return cell_str


def _extract_output(output: Dict[str, Any]) -> List[str]:
    """
    Extract the output from a Jupyter notebook cell.

    Parameters
    ----------
    output : Dict[str, Any]
        The output dictionary from a Jupyter notebook cell.

    Returns
    -------
    List[str]
        The output as a list of strings.

    Raises
    ------
    ValueError
        If an unknown output type is encountered.
    """
    output_type = output["output_type"]

    if output_type == "stream":
        return output["text"]

    if output_type in ("execute_result", "display_data"):
        return output["data"]["text/plain"]

    if output_type == "error":
        return [f"Error: {output['ename']}: {output['evalue']}"]

    raise ValueError(f"Unknown output type: {output_type}")
