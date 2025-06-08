"""Command-line interface for the Gitingest package."""

# pylint: disable=no-value-for-parameter

import asyncio
import os
import gzip
from pathlib import Path
from typing import Optional, Tuple
import click

from gitingest.config import MAX_FILE_SIZE, OUTPUT_FILE_NAME
from gitingest.entrypoint import ingest_async
from gitingest.output_utils import write_digest


@click.command()
@click.argument("source", type=str)
@click.argument("output", type=str, required=False, default=OUTPUT_FILE_NAME)
@click.option("--max-size", "-s", default=MAX_FILE_SIZE, help="Maximum file size to process in bytes")
@click.option("--exclude-pattern", "-e", multiple=True, help="Patterns to exclude")
@click.option("--include-pattern", "-i", multiple=True, help="Patterns to include")
@click.option("--branch", "-b", default=None, help="Branch to clone and ingest")
@click.option("--parallel/--no-parallel", default=(os.cpu_count() or 1) > 2, help="Scan files with multiple threads")
@click.option("--incremental", is_flag=True, help="Use disk cache to skip unchanged files")
@click.option("--compress", is_flag=True, help="Write gzip compressed output")
def main(
    source: str,
    output: str,
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
    parallel: bool,
    compress: bool,
):
    """
     Main entry point for the CLI. This function is called when the CLI is run as a script.

    It calls the async main function to run the command.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.
    output : str, optional
        The path where the output file will be written. If not specified, the output will be written
        to a file named `<repo_name>.txt` in the current directory.
    max_size : int
        The maximum file size to process, in bytes. Files larger than this size will be ignored.
    exclude_pattern : Tuple[str, ...]
        A tuple of patterns to exclude during the analysis. Files matching these patterns will be ignored.
    include_pattern : Tuple[str, ...]
        A tuple of patterns to include during the analysis. Only files matching these patterns will be processed.
    branch : str, optional
        The branch to clone (optional).
    parallel : bool
        Enable multithreaded scanning.
    incremental : bool
        Use on-disk cache to skip unchanged files.
    compress : bool
        Write gzip compressed output.
    parallel : bool
        Enable multithreaded scanning.
    incremental : bool
        Use on-disk cache to skip unchanged files.
    compress : bool
        Write gzip compressed output.
    """
    # Main entry point for the CLI. This function is called when the CLI is run as a script.
    asyncio.run(
        _async_main(
            source,
            output,
            max_size,
            exclude_pattern,
            include_pattern,
            branch,
            parallel,
            incremental,
            compress,
        )
    )


async def _async_main(
    source: str,
    output: str,
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
    parallel: bool,
    incremental: bool,

    compress: bool,
) -> None:
    """
    Analyze a directory or repository and create a text dump of its contents.

    This command analyzes the contents of a specified source directory or repository, applies custom include and
    exclude patterns, and generates a text summary of the analysis which is then written to an output file.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.
    output : str, optional
        The path where the output file will be written. If not specified, the output will be written
        to a file named `<repo_name>.txt` in the current directory.
    max_size : int
        The maximum file size to process, in bytes. Files larger than this size will be ignored.
    exclude_pattern : Tuple[str, ...]
        A tuple of patterns to exclude during the analysis. Files matching these patterns will be ignored.
    include_pattern : Tuple[str, ...]
        A tuple of patterns to include during the analysis. Only files matching these patterns will be processed.
    branch : str, optional
        The branch to clone (optional).

    Raises
    ------
    Abort
        If there is an error during the execution of the command, this exception is raised to abort the process.
    """
    try:
        exclude_patterns = set(exclude_pattern)
        include_patterns = set(include_pattern)
        if not output:
            output = OUTPUT_FILE_NAME
        summary, _, _ = await ingest_async(
        summary, tree, content = await ingest_async(
            source,
            max_size,
            include_patterns,
            exclude_patterns,
            branch,
            output=output,
            parallel=parallel,
            incremental=incremental,
            compress=compress,
        )

        click.echo(f"Analysis complete! Output written to: {output}")
            output=None,
        )

        text = tree + "\n" + content
        if compress:
            gz_path = Path(str(output) + ".gz")
            with gzip.open(gz_path, "wt", encoding="utf-8") as f:
                f.write(text)
            out_name = str(gz_path)
        else:
            write_digest(text, Path(output), compress=False)
            out_name = str(output)
        click.echo(f"Analysis complete! Output written to: {out_name}")
        click.echo("\nSummary:")
        click.echo(summary)

    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
