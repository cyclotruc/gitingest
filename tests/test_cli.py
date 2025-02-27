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


def test_cli_tag_option():
    """Test that the --tag flag works correctly."""
    runner = CliRunner()
    with patch("gitingest.cli._async_main") as mock_async_main:
        # Test with tag option
        result = runner.invoke(main, ["./", "--tag", "v1.0.0"])
        assert result.exit_code == 0
        mock_async_main.assert_called_with(
            source="./",
            output=None,
            max_size=10485760,
            exclude_pattern=(),
            include_pattern=(),
            branch=None,
            tag="v1.0.0",
            include_submodules=False,
        )


def test_cli_tag_and_branch_conflict():
    """Test that specifying both tag and branch raises an error."""
    runner = CliRunner()
    with patch("gitingest.cli.ingest_async", side_effect=ValueError("Cannot specify both branch and tag")):
        result = runner.invoke(main, ["./", "--tag", "v1.0.0", "--branch", "main"])
        assert result.exit_code != 0
        assert "Error: Cannot specify both branch and tag" in result.output
