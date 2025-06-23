"""Tests for the Gitingest CLI."""

import os
from inspect import signature
from pathlib import Path
from typing import List

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner, Result

from gitingest.cli import main
from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_NAME


@pytest.mark.parametrize(
    "cli_args, expect_file",
    [
        pytest.param(["./"], True, id="default-options"),
        pytest.param(
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
            True,
            id="custom-options",
        ),
    ],
)
def test_cli_writes_file(tmp_path: Path, monkeypatch: MonkeyPatch, cli_args: List[str], expect_file: bool) -> None:
    """Run the CLI and verify that the SARIF file is created (or not)."""
    # Work inside an isolated temp directory
    monkeypatch.chdir(tmp_path)

    result = _invoke_isolated_cli_runner(cli_args)

    assert result.exit_code == 0, result.stderr

    # Summary line should be on STDOUT
    stdout_lines = result.stdout.splitlines()
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_NAME}" in stdout_lines

    # File side-effect
    sarif_file = tmp_path / OUTPUT_FILE_NAME
    assert sarif_file.exists() is expect_file, f"{OUTPUT_FILE_NAME} existence did not match expectation"


def test_cli_with_stdout_output() -> None:
    """Test CLI invocation with output directed to STDOUT."""
    # Clean up any existing digest.txt file before test
    if os.path.exists(OUTPUT_FILE_NAME):
        os.remove(OUTPUT_FILE_NAME)

    try:
        result = _invoke_isolated_cli_runner(["./", "--output", "-", "--exclude-pattern", "tests/"])

        # ─── core expectations (stdout) ────────────────────────────────────-
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}, stderr: {result.stderr}"
        assert "---" in result.stdout, "Expected file separator '---' not found in STDOUT"
        assert (
            "src/gitingest/cli.py" in result.stdout
        ), "Expected content (e.g., src/gitingest/cli.py) not found in STDOUT"
        assert not os.path.exists(OUTPUT_FILE_NAME), f"Output file {OUTPUT_FILE_NAME} was unexpectedly created."

        # ─── the summary must *not* pollute STDOUT, must appear on STDERR ───
        summary = "Analysis complete! Output sent to stdout."
        stdout_lines = result.stdout.splitlines()
        stderr_lines = result.stderr.splitlines()
        assert summary not in stdout_lines, "Unexpected summary message found in STDOUT"
        assert summary in stderr_lines, "Expected summary message not found in STDERR"
        assert f"Output written to: {OUTPUT_FILE_NAME}" not in stderr_lines
    finally:
        # Clean up any digest.txt file that might have been created during test
        if os.path.exists(OUTPUT_FILE_NAME):
            os.remove(OUTPUT_FILE_NAME)


def _invoke_isolated_cli_runner(args: List[str]) -> Result:
    """Return a CliRunner that keeps stderr apart on Click 8.0-8.1."""
    kwargs = {}
    if "mix_stderr" in signature(CliRunner.__init__).parameters:
        kwargs["mix_stderr"] = False  # Click 8.0–8.1
    runner = CliRunner(**kwargs)
    return runner.invoke(main, args)
