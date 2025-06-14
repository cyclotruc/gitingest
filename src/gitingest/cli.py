"""Command-line interface for the Gitingest package."""

# pylint: disable=no-value-for-parameter

import asyncio
from typing import Optional, Tuple

import click

from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_NAME
from gitingest.entrypoint import ingest_async


@click.command()
@click.argument("source", type=str, default=".")
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path (default: <repo_name>.txt in current directory)",
)
@click.option(
    "--max-size",
    "-s",
    default=MAX_FILE_SIZE,
    help="Maximum file size to process in bytes",
)
@click.option(
    "--exclude-pattern",
    "-e",
    multiple=True,
    help=(
        "Patterns to exclude. Handles Python's arbitrary subset of Unix shell-style "
        "wildcards. See: https://docs.python.org/3/library/fnmatch.html"
    ),
)
@click.option(
    "--include-pattern",
    "-i",
    multiple=True,
    help=(
        "Patterns to include. Handles Python's arbitrary subset of Unix shell-style "
        "wildcards. See: https://docs.python.org/3/library/fnmatch.html"
    ),
)
@click.option("--branch", "-b", default=None, help="Branch to clone and ingest")
def main(
    source: str,
    output: Optional[str],
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
):
    """
    Main entry point for the CLI. This function is called when the CLI is run as a script.

    It calls the async main function to run the command.

    Parameters
    ----------
    source : str
        A directory path or a Git repository URL.
    output : str, optional
        Output file path. Defaults to `<repo_name>.txt`.
    max_size : int
        Maximum file size (in bytes) to consider.
    exclude_pattern : Tuple[str, ...]
        Glob patterns for pruning the file set.
    include_pattern : Tuple[str, ...]
        Glob patterns for including files in the output.
    branch : str, optional
        Specific branch to ingest (defaults to the repository's default).
    """

    asyncio.run(
        _async_main(
            source=source,
            output=output,
            max_size=max_size,
            exclude_pattern=exclude_pattern,
            include_pattern=include_pattern,
            branch=branch,
        )
    )


async def _async_main(
    source: str,
    output: Optional[str],
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
) -> None:
    """
    Analyze a directory or repository and create a text dump of its contents.

    This command analyzes the contents of a specified source directory or repository, applies custom include and
    exclude patterns, and generates a text summary of the analysis which is then written to an output file.

    Parameters
    ----------
    source : str
        A directory path or a Git repository URL.
    output : str, optional
        Output file path. Defaults to `<repo_name>.txt`.
    max_size : int
        Maximum file size (in bytes) to consider.
    exclude_pattern : Tuple[str, ...]
        Glob patterns for pruning the file set.
    include_pattern : Tuple[str, ...]
        Glob patterns for including files in the output.
    branch : str, optional
        Specific branch to ingest (defaults to the repository's default).

    Raises
    ------
    Abort
        If there is an error during the execution of the command, this exception is raised to abort the process.
    """
    try:
        # Normalise pattern containers (the ingest layer expects sets)
        exclude_patterns = set(exclude_pattern)
        include_patterns = set(include_pattern)

        # Choose a default output path if none provided
        if output is None:
            output = OUTPUT_FILE_NAME

        summary, _, _ = await ingest_async(
            source=source,
            max_file_size=max_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch,
            output=output,
        )

        click.echo(f"Analysis complete! Output written to: {output}")
        click.echo("\nSummary:")
        click.echo(summary)

    except Exception as exc:
        # Convert any exception into Click.Abort so that exit status is non-zero
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort() from exc


if __name__ == "__main__":
    main()
