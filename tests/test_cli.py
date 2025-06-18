"""Tests for the gitingest cli."""

import os
from inspect import signature

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
        ],
    )
    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_NAME}" in output_lines
    assert os.path.exists(OUTPUT_FILE_NAME), f"Output file was not created at {OUTPUT_FILE_NAME}"

    os.remove(OUTPUT_FILE_NAME)


def test_cli_with_stdout_output():
    """Test CLI invocation with output directed to STDOUT."""

    kwargs = {}
    if "mix_stderr" in signature(CliRunner.__init__).parameters:
        kwargs["mix_stderr"] = (
            False  # Click < 8.2 (https://click.palletsprojects.com/en/stable/changes/#version-8-2-0)
        )

    runner = CliRunner(**kwargs)
    result = runner.invoke(main, ["./", "--output", "-", "--exclude-pattern", "tests/"])

    assert result.exit_code == 0, f"CLI exited with code {result.exit_code}, stderr: {result.stderr}"
    assert "---" in result.output, "Expected file separator '---' not found in STDOUT"
    assert "src/gitingest/cli.py" in result.output, "Expected content (e.g., src/gitingest/cli.py) not found in STDOUT"
    assert not os.path.exists(OUTPUT_FILE_NAME), f"Output file {OUTPUT_FILE_NAME} was unexpectedly created."
    assert "Analysis complete!  Output sent to stdout." not in result.output
    assert "Analysis complete!" in result.stderr, "Expected summary message 'Analysis complete!' not found in STDERR"
    assert f"Output written to: {OUTPUT_FILE_NAME}" not in result.stderr
