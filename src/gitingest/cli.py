"""Command-line interface for the Gitingest package."""

# pylint: disable=no-value-for-parameter

import asyncio
from typing import Optional, Tuple
from pathlib import Path

import click

from gitingest.config import MAX_FILE_SIZE_BYTES, OUTPUT_FILE_NAME
from gitingest.entrypoint import ingest_async
from gitingest.ingestion import ingest_query
from gitingest.query_parsing import parse_query
from gitingest.utils.exceptions import handle_exceptions


@click.command()
@click.argument("source", type=str, default=".")
@click.option("--output", "-o", default=None, help=f"Output file path (used only if cloud upload is disabled/fails; defaults to {OUTPUT_FILE_NAME})")
@click.option("--max-size", "-s", default=MAX_FILE_SIZE_BYTES, help="Maximum file size to process in bytes")
@click.option("--exclude-pattern", "-e", multiple=True, help="Patterns to exclude")
@click.option("--include-pattern", "-i", multiple=True, help="Patterns to include")
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

    It calls the synchronous main function to run the command.

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
    """
    # Main entry point for the CLI. This function is called when the CLI is run as a script.
    # Directly call the synchronous logic now, async might be overkill if not interacting with web server directly here.
    _sync_main(source, output, max_size, exclude_pattern, include_pattern, branch)


@handle_exceptions()
def _sync_main(
    source: str,
    output: Optional[str],
    max_size: int, # Note: max_size is not directly used by parse_query/ingest_query yet
    exclude_pattern: Tuple[str, ...],
    include_pattern: Tuple[str, ...],
    branch: Optional[str],
) -> None:
    """
    Synchronous version of the main CLI logic.
    Parses query, ingests, and handles output (file or URL).
    """
    # Construct the query string or dictionary for parse_query
    # Assuming 'source' is the primary input like a URL or path
    query_input = source
    # We might need to refine how options like branch, include/exclude are passed to parse_query
    # For now, assume parse_query primarily uses the source string
    # Ideally, parse_query would accept these other parameters too.
    # Let's manually add them to the query object for now if they exist.

    ingestion_query = parse_query(query_input)

    # Apply CLI options to the parsed query object if they weren't handled by parse_query
    if branch and not ingestion_query.branch:
        ingestion_query.branch = branch
    if exclude_pattern:
        if ingestion_query.ignore_patterns is None:
            ingestion_query.ignore_patterns = set()
        ingestion_query.ignore_patterns.update(exclude_pattern)
    if include_pattern:
        if ingestion_query.include_patterns is None:
            ingestion_query.include_patterns = set()
        ingestion_query.include_patterns.update(include_pattern)
    # We might need to pass max_size to ingestion_query or ingest_query if needed

    # --- Perform Ingestion --- 
    summary, tree, content_or_url = ingest_query(ingestion_query)

    # --- Handle Output --- 
    click.echo("Summary:")
    click.echo(summary)
    click.echo("\nDirectory Structure:")
    click.echo(tree)

    is_url = isinstance(content_or_url, str) and content_or_url.startswith("http")

    if is_url:
        click.echo(f"\nContent digest uploaded to: {content_or_url}")
    elif content_or_url is not None:
        # Determine output path
        if output:
            output_path = Path(output)
        else:
            # Default filename based on slug or generic name
            default_name = ingestion_query.slug if ingestion_query.slug else OUTPUT_FILE_NAME
            output_path = Path.cwd() / default_name
            # Ensure a .txt extension if not present in slug
            if output_path.suffix != '.txt':
                 output_path = output_path.with_suffix('.txt')
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Combine all parts for the file output
            full_content = f"{summary}\n\n{tree}\n\n{content_or_url}"
            output_path.write_text(full_content, encoding="utf-8")
            click.echo(f"\nContent digest written to: {output_path.resolve()}")
        except Exception as e:
             click.echo(f"\nError writing content digest to {output_path.resolve()}: {e}", err=True)
             # Optionally re-raise or handle differently
    else:
        # Handle case where upload failed and ingest_query returned None for the third element
        click.echo("\nContent digest generation succeeded, but upload failed. No output generated.", err=True)


if __name__ == "__main__":
    main()
