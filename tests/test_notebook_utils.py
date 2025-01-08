""" Tests for the notebook_utils module. """

import pytest

from gitingest.notebook_utils import process_notebook


def test_process_notebook_all_cells(write_notebook):
    """
    Test a notebook containing markdown, code, and raw cells.

    - Markdown/raw cells => triple-quoted
    - Code cells => remain normal code
    - For 1 markdown + 1 raw => 2 triple-quoted blocks => 4 occurrences of triple-quotes.
    """
    notebook_content = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Markdown cell"]},
            {"cell_type": "code", "source": ['print("Hello Code")']},
            {"cell_type": "raw", "source": ["<raw content>"]},
        ]
    }
    nb_path = write_notebook("all_cells.ipynb", notebook_content)
    result = process_notebook(nb_path)

    assert result.count('"""') == 4, "Expected 4 triple-quote occurrences for 2 blocks."

    # Check that markdown and raw content are inside triple-quoted blocks
    assert "# Markdown cell" in result
    assert "<raw content>" in result

    # Check code cell is present and not wrapped in triple quotes
    assert 'print("Hello Code")' in result
    assert '"""\nprint("Hello Code")\n"""' not in result


def test_process_notebook_with_worksheets(write_notebook):
    """
    Test a notebook containing the 'worksheets' key (deprecated as of IPEP-17).

    - Should raise a DeprecationWarning.
    - We process only the first (and only) worksheet's cells.
    - The resulting content matches an equivalent notebook with "cells" at top level.
    """
    with_worksheets = {
        "worksheets": [
            {
                "cells": [
                    {"cell_type": "markdown", "source": ["# Markdown cell"]},
                    {"cell_type": "code", "source": ['print("Hello Code")']},
                    {"cell_type": "raw", "source": ["<raw content>"]},
                ]
            }
        ]
    }
    without_worksheets = with_worksheets["worksheets"][0]  # same, but no 'worksheets' key at top

    nb_with = write_notebook("with_worksheets.ipynb", with_worksheets)
    nb_without = write_notebook("without_worksheets.ipynb", without_worksheets)

    with pytest.warns(DeprecationWarning, match="Worksheets are deprecated as of IPEP-17."):
        result_with = process_notebook(nb_with)

    # No warnings here
    result_without = process_notebook(nb_without)

    assert result_with == result_without, "Both notebooks should produce identical content."


def test_process_notebook_multiple_worksheets(write_notebook):
    """
    Test a notebook containing multiple 'worksheets'.

    If multiple worksheets are present:
    - Only process the first sheet's cells.
    - DeprecationWarning for worksheets
    - UserWarning for ignoring extra worksheets
    """
    multi_worksheets = {
        "worksheets": [
            {"cells": [{"cell_type": "markdown", "source": ["# First Worksheet"]}]},
            {"cells": [{"cell_type": "code", "source": ['print("Ignored Worksheet")']}]},
        ]
    }

    # Single-worksheet version (only the first)
    single_worksheet = {
        "worksheets": [
            {"cells": [{"cell_type": "markdown", "source": ["# First Worksheet"]}]},
        ]
    }

    nb_multi = write_notebook("multiple_worksheets.ipynb", multi_worksheets)
    nb_single = write_notebook("single_worksheet.ipynb", single_worksheet)

    with pytest.warns(DeprecationWarning, match="Worksheets are deprecated as of IPEP-17."):
        with pytest.warns(UserWarning, match="Multiple worksheets are not supported."):
            result_multi = process_notebook(nb_multi)

    with pytest.warns(DeprecationWarning, match="Worksheets are deprecated as of IPEP-17."):
        result_single = process_notebook(nb_single)

    # The second worksheet (with code) should have been ignored
    assert result_multi == result_single, "Second worksheet was ignored, results match."


def test_process_notebook_code_only(write_notebook):
    """
    Test a notebook containing only code cells.

    No triple quotes should appear.
    """
    notebook_content = {
        "cells": [
            {"cell_type": "code", "source": ["print('Code Cell 1')"]},
            {"cell_type": "code", "source": ["x = 42"]},
        ]
    }
    nb_path = write_notebook("code_only.ipynb", notebook_content)
    result = process_notebook(nb_path)

    # No triple quotes
    assert '"""' not in result
    assert "print('Code Cell 1')" in result
    assert "x = 42" in result


def test_process_notebook_markdown_only(write_notebook):
    """
    Test a notebook with 2 markdown cells.

    2 markdown cells => each becomes 1 triple-quoted block => 2 blocks => 4 triple quotes.
    """
    notebook_content = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Markdown Header"]},
            {"cell_type": "markdown", "source": ["Some more markdown."]},
        ]
    }
    nb_path = write_notebook("markdown_only.ipynb", notebook_content)
    result = process_notebook(nb_path)

    assert result.count('"""') == 4, "Two markdown cells => two triple-quoted blocks => 4 triple quotes total."
    assert "# Markdown Header" in result
    assert "Some more markdown." in result


def test_process_notebook_raw_only(write_notebook):
    """
    Test a notebook with 2 raw cells.

    2 raw cells => 2 blocks => 4 triple quotes.
    """
    notebook_content = {
        "cells": [
            {"cell_type": "raw", "source": ["Raw content line 1"]},
            {"cell_type": "raw", "source": ["Raw content line 2"]},
        ]
    }
    nb_path = write_notebook("raw_only.ipynb", notebook_content)
    result = process_notebook(nb_path)

    # 2 raw cells => 2 triple-quoted blocks => 4 occurrences
    assert result.count('"""') == 4
    assert "Raw content line 1" in result
    assert "Raw content line 2" in result


def test_process_notebook_empty_cells(write_notebook):
    """
    Test that cells with an empty 'source' are skipped entirely.

    4 cells but 3 are empty => only 1 non-empty cell => 1 triple-quoted block => 2 quotes.
    """
    notebook_content = {
        "cells": [
            {"cell_type": "markdown", "source": []},
            {"cell_type": "code", "source": []},
            {"cell_type": "raw", "source": []},
            {"cell_type": "markdown", "source": ["# Non-empty markdown"]},
        ]
    }
    nb_path = write_notebook("empty_cells.ipynb", notebook_content)
    result = process_notebook(nb_path)

    # Only one non-empty markdown cell => 1 block => 2 triple quotes
    assert result.count('"""') == 2
    assert "# Non-empty markdown" in result


def test_process_notebook_invalid_cell_type(write_notebook):
    """
    Test a notebook with an unknown cell type.

    Should raise a ValueError.
    """
    notebook_content = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Valid markdown"]},
            {"cell_type": "unknown", "source": ["Unrecognized cell type"]},
        ]
    }
    nb_path = write_notebook("invalid_cell_type.ipynb", notebook_content)

    with pytest.raises(ValueError, match="Unknown cell type: unknown"):
        process_notebook(nb_path)
