""" Tests for the gitingest cli """

import os

from click.testing import CliRunner

from gitingest.cli import main
from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_PATH


def test_cli_with_default_options():
    runner = CliRunner()
    result = runner.invoke(main, ["./"])
    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_PATH}" in output_lines
    assert os.path.exists(OUTPUT_FILE_PATH), f"Output file was not created at {OUTPUT_FILE_PATH}"

    os.remove(OUTPUT_FILE_PATH)


def test_cli_with_options():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "./",
            "--output",
            OUTPUT_FILE_PATH,
            "--max-size",
            MAX_FILE_SIZE,
            "--exclude-pattern",
            "tests/",
            "--include-pattern",
            "src/",
        ],
    )
    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_PATH}" in output_lines
    assert os.path.exists(OUTPUT_FILE_PATH), f"Output file was not created at {OUTPUT_FILE_PATH}"

    os.remove(OUTPUT_FILE_PATH)
