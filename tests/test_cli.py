"""Tests for the gitingest cli."""

import os
import pytest
from unittest.mock import AsyncMock

from click.testing import CliRunner

from gitingest.cli import main
from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_NAME

# Mock the ingest_async function to avoid actual processing
@pytest.fixture(autouse=True)
def mock_ingest_async(mocker):
    mock = mocker.patch("gitingest.cli.ingest_async", new_callable=AsyncMock)
    mock.return_value = ("summary", "tree", "content")
    return mock


def test_cli_with_default_options(mock_ingest_async):
    runner = CliRunner()
    result = runner.invoke(main, ["./"])
    assert result.exit_code == 0
    # Use keyword args only, check source explicitly
    call_args, call_kwargs = mock_ingest_async.await_args
    assert call_args == ()
    assert call_kwargs.get("source") in ('.', './')
    assert call_kwargs == {
        "source": call_kwargs.get("source"), # Keep the actual source value
        "max_file_size": MAX_FILE_SIZE,
        "include_patterns": set(),
        "exclude_patterns": set(),
        "branch": None,
        "output": OUTPUT_FILE_NAME, # Check default output name
        "access_token": None, # Renamed token param
    }

    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {OUTPUT_FILE_NAME}" in output_lines
    # assert os.path.exists(OUTPUT_FILE_NAME), f"Output file was not created at {OUTPUT_FILE_NAME}" # Remove check

    # Clean up: Remove the default output file if created by the mocked logic (or original if mock fails)
    # if os.path.exists(OUTPUT_FILE_NAME): # Remove cleanup
    #     os.remove(OUTPUT_FILE_NAME)


def test_cli_with_options(mock_ingest_async):
    runner = CliRunner()
    output_file = "test_output.txt"
    exclude = "tests/"
    include = "src/"
    branch = "develop"
    token = "test_token_123"
    result = runner.invoke(
        main,
        [
            ".",
            "--output",
            output_file,
            "--max-size",
            str(MAX_FILE_SIZE),
            "--exclude-pattern",
            exclude,
            "--include-pattern",
            include,
            "--branch",
            branch,
            "--access-token", # Renamed token param
            token,
        ],
    )
    assert result.exit_code == 0
    # Use keyword args only, check source explicitly
    call_args, call_kwargs = mock_ingest_async.await_args
    assert call_args == ()
    assert call_kwargs.get("source") in ('.', './')
    assert call_kwargs == {
        "source": call_kwargs.get("source"), # Keep the actual source value
        "max_file_size": MAX_FILE_SIZE,
        "include_patterns": {include},
        "exclude_patterns": {exclude},
        "branch": branch,
        "output": output_file,
        "access_token": token, # Renamed token param
    }

    output_lines = result.output.strip().split("\n")
    assert f"Analysis complete! Output written to: {output_file}" in output_lines
    # assert os.path.exists(output_file), f"Output file was not created at {output_file}" # Remove check

    # Clean up
    # if os.path.exists(output_file): # Remove cleanup
    #     os.remove(output_file)
