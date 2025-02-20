""" Tests for the gitingest cli """

import os

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
