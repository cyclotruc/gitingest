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
@click.argument("source", type=str, default=".")
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path. Defaults to digest.txt. Use '-' to output to stdout.",
)
@click.option(
    "--max-size", "-s", default=MAX_FILE_SIZE, help="Maximum file size to process in bytes"
)
@click.option(
    "--exclude-pattern",
    "-e",
    multiple=True,
    help="Patterns to exclude. See: https://docs.python.org/3/library/fnmatch.html",
)
@click.option(
    "--include-pattern",
    "-i",
    multiple=True,
    help="Patterns to include. See: https://docs.python.org/3/library/fnmatch.html",
)
@click.option("--branch", "-b", default=None, help="Branch to clone and ingest")
@click.option(
    "--token",
    "-t",
    envvar="GITHUB_TOKEN",
    default=None,
    help="GitHub PAT for private repos. Can also be set via GITHUB_TOKEN env var.",
)
@click.option(
    "--parallel/--no-parallel",
    default=(os.cpu_count() or 1) > 2,
    help="Scan files with multiple threads.",
)
@click.option("--incremental", is_flag=True, help="Use disk cache to skip unchanged files.")
@click.option("--compress", is_flag=True, help="Write gzip compressed output.")
@click.option("--stream", is_flag=True, help="Download via GitHub API instead of git clone.")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "jsonl"]),
    default="text",
    help="The output format for the digest.",
)
def main(
    source: str,
    output: Optional[str],
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
    token: Optional[str],
    parallel: bool,
    incremental: bool,
    compress: bool,
    stream: bool,
    output_format: str,
) -> None:
    """Main entry point for the CLI."""
    asyncio.run(
        _async_main(
            source=source,
            output=output,
            max_size=max_size,
            exclude_pattern=exclude_pattern,
            include_pattern=include_pattern,
            branch=branch,
            token=token,
            parallel=parallel,
            incremental=incremental,
            compress=compress,
            stream=stream,
            output_format=output_format,
        )
    )


async def _async_main(  # pylint: disable=too-many-arguments,too-many-locals
    source: str,
    output: Optional[str],
    max_size: int,
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
    token: Optional[str],
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

        if output == "-":
            click.echo("Analyzing source, preparing output for stdout...", err=True)
        else:
            out_name = output if output else OUTPUT_FILE_NAME
            if compress and not out_name.endswith(".gz"):
                out_name += ".gz"
            click.echo(f"Analyzing source, output will be written to '{out_name}'...", err=True)

        summary, tree, content = await ingest_async(
            source,
            max_file_size=max_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch,
            token=token,
            output=None,  # We handle writing the output ourselves
            parallel=parallel,
            incremental=incremental,
            compress=compress,
            stream=stream,
            output_format=output_format,
        )

        text = tree + "\n" + content

        if output == "-":  # Handle stdout case
            click.echo(text)
            click.echo("\n--- Summary ---", err=True)
            click.echo(summary, err=True)
            click.echo("--- End Summary ---", err=True)
            click.echo("Analysis complete! Output sent to stdout.", err=True)
        else:  # Handle file output case
            output_path = Path(output if output else OUTPUT_FILE_NAME)
            write_digest(text, output_path, compress)
            final_out_name = str(output_path)
            if compress and not final_out_name.endswith(".gz"):
                final_out_name += ".gz"

            click.echo(f"Analysis complete! Output written to: {final_out_name}")
            click.echo("\nSummary:")
            click.echo(summary)

    except Exception as exc:
        # Convert any exception into Click.Abort so that exit status is non-zero
        click.echo(f"Error: {exc}", err=True)
        raise click.Abort() from exc


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()