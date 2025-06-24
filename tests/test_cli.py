"""Tests for the gitingest CLI."""

# pylint: disable=too-many-arguments,too-many-positional-arguments

import os
from unittest.mock import patch
from click.testing import CliRunner
from gitingest.cli import main
from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_NAME


async def _stub_ingest_async(
    source: str,
    max_file_size: int = MAX_FILE_SIZE,
    include_patterns=None,
    exclude_patterns=None,
    branch=None,
    output: str | None = None,
    parallel: bool = False,
    incremental: bool = False,
    compress: bool = False,
    stream: bool = False,
):
    # pylint: disable=unused-argument,too-many-arguments
    path = output or OUTPUT_FILE_NAME
    with open(path, "w", encoding="utf-8") as f:
        f.write("dummy")
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write("dummy")
    return "summary", "tree", "content"


def test_cli_with_default_options():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch("gitingest.cli.ingest_async", new=_stub_ingest_async):
            result = runner.invoke(main, ["./", OUTPUT_FILE_NAME])
        output_lines = result.output.strip().split("\n")
        assert f"Analysis complete! Output written to: {OUTPUT_FILE_NAME}" in output_lines
        assert os.path.exists(OUTPUT_FILE_NAME), f"Output file was not created at {OUTPUT_FILE_NAME}"


def test_cli_with_options():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch("gitingest.cli.ingest_async", new=_stub_ingest_async):
            result = runner.invoke(
                main,
                [
                    "./",
                    OUTPUT_FILE_NAME,
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
