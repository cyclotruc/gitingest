# pylint: disable=no-value-for-parameter

"""Command line interface for the ``gitingest`` package."""

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
@click.option("--stream", is_flag=True, help="Download via GitHub API instead of git")
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
    except Exception as exc:  # pragma: no cover - CLI error handling
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
