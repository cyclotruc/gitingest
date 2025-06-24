# pylint: disable=no-value-for-parameter

"""Command line interface for the ``gitingest`` package."""

import asyncio
import os
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
@click.option("--stream", is_flag=True, help="Download via GitHub API instead of git")
@click.option("--format", "-f", "output_format", type=click.Choice(['text', 'jsonl']), default='text', help="The output format for the digest.")
def main(
    source: str,
    output: str,
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
    parallel: bool,
    incremental: bool,
    compress: bool,
    stream: bool,
    output_format: str,
) -> None:
    """Main entry point for the CLI."""
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
            stream,
            output_format,
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
    stream: bool,
    output_format: str,
) -> None:
    """Analyze a directory or repository and create a text dump of its contents."""
    try:
        exclude_patterns = set(exclude_pattern)
        include_patterns = set(include_pattern)

        summary, tree, content = await ingest_async(
            source,
            max_size,
            include_patterns,
            exclude_patterns,
            branch,
            output=None,
            parallel=parallel,
            incremental=incremental,
            compress=compress,
            stream=stream,
            output_format=output_format,
        )

        text = tree + "\n" + content
        output_path = Path(output)

        # Single call to our robust utility function
        write_digest(text, output_path, compress)

        # Determine the final output name for the user message
        if compress:
            out_name = str(output_path) + ".gz"
        else:
            out_name = str(output_path)

        click.echo(f"Analysis complete! Output written to: {out_name}")
        click.echo("\nSummary:")
        click.echo(summary)
    except Exception as exc:  # pragma: no cover - CLI error handling
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
