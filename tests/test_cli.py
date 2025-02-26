""" Tests for the gitingest cli """

import os
from unittest.mock import patch

from click.testing import CliRunner

from gitingest.cli import main
from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_NAME


def test_cli_with_default_options():
    runner = CliRunner()
    result = runner.invoke(main, ["./"])
    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_NAME}" in output_lines
    assert os.path.exists(OUTPUT_FILE_NAME), f"Output file was not created at {OUTPUT_FILE_NAME}"

    os.remove(OUTPUT_FILE_NAME)


def test_cli_with_options():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "./",
            "--output",
            str(OUTPUT_FILE_NAME),
            "--max-size",
            str(MAX_FILE_SIZE),
            "--exclude-pattern",
            "tests/",
            "--include-pattern",
            "src/",
            "--include-submodules",
        ],
    )
    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_NAME}" in output_lines
    assert os.path.exists(OUTPUT_FILE_NAME), f"Output file was not created at {OUTPUT_FILE_NAME}"

    os.remove(OUTPUT_FILE_NAME)


def test_cli_submodules_flag():
    """Test that the --include-submodules flag works correctly."""
    runner = CliRunner()
    with patch("gitingest.cli._async_main") as mock_async_main:
        # Test with flag
        result = runner.invoke(main, ["./", "--include-submodules"])
        assert result.exit_code == 0
        mock_async_main.assert_called_with(
            "./",
            None,
            10485760,
            (),
            (),
            None,
            True,  # include_submodules
        )

        # Test without flag
        result = runner.invoke(main, ["./"])
        assert result.exit_code == 0
        mock_async_main.assert_called_with(
            "./",
            None,
            10485760,
            (),
            (),
            None,
            False,  # include_submodules
        )
