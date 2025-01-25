"""Command-line interface for the Gitingest package."""

# pylint: disable=no-value-for-parameter
import asyncio
from pathlib import Path

import click

from gitingest.config import MAX_FILE_SIZE
from gitingest.query_parser import _parse_patterns, parse_ignore_file
from gitingest.repository_ingest import ingest


@click.command()
@click.argument("source", type=str, default=".")
@click.option("--output", "-o", default=None, help="Output file path (default: <repo_name>.txt in current directory)")
@click.option("--max-size", "-s", default=MAX_FILE_SIZE, help="Maximum file size to process in bytes")
@click.option("--exclude-pattern", "-e", multiple=True, help="Patterns to exclude (space-separated patterns allowed)")
@click.option("--include-pattern", "-i", multiple=True, help="Patterns to include (space-separated patterns allowed)")
@click.option("--ignore-file", default=".gitingestignore", help="Path to ignore file (default: .gitingestignore)")
@click.option("--branch", "-b", default=None, help="Branch to clone and ingest")
def main(
    source: str,
    output: str | None,
    max_size: int,
    exclude_pattern: tuple[str, ...],
    include_pattern: tuple[str, ...],
    ignore_file: str,
    branch: str | None,
):
    """
    Main entry point for the CLI.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.
    output : str | None
        The path where the output file will be written. If not specified, the output
        will be written to a file named `<repo_name>.txt` in the current directory.
    max_size : int
        The maximum file size to process, in bytes. Files larger than this size will be ignored.
    exclude_pattern : tuple[str, ...]
        A tuple of patterns to exclude during the analysis. Files matching these patterns will be ignored.
    include_pattern : tuple[str, ...]
        A tuple of patterns to include during the analysis. Only files matching these patterns will be processed.
    ignore_file : str
        Path to the ignore file containing additional patterns to exclude.
    branch : str | None
        The branch to clone (optional).
    """
    asyncio.run(async_main(source, output, max_size, exclude_pattern, include_pattern, ignore_file, branch))


async def async_main(
    source: str,
    output: str | None,
    max_size: int,
    exclude_pattern: tuple[str, ...],
    include_pattern: tuple[str, ...],
    ignore_file: str,
    branch: str | None,
) -> None:
    """
    Analyze a directory or repository and create a text dump of its contents.

    This command analyzes the contents of a specified source directory or repository,
    applies custom include and exclude patterns, and generates a text summary of the
    analysis which is then written to an output file.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.
    output : str | None
        The path where the output file will be written. If not specified, the output
        will be written to a file named `<repo_name>.txt` in the current directory.
    max_size : int
        The maximum file size to process, in bytes. Files larger than this size will be ignored.
    exclude_pattern : tuple[str, ...]
        A tuple of patterns to exclude during the analysis. Files matching these patterns will be ignored.
    include_pattern : tuple[str, ...]
        A tuple of patterns to include during the analysis. Only files matching these patterns will be processed.
    ignore_file : str
        Path to the ignore file containing additional patterns to exclude.
    branch : str | None
        The branch to clone (optional).

    Raises
    ------
    Abort
        If there is an error during the execution of the command, this exception is raised to abort the process.
    """
    try:
        # Get repository name from source path
        repo_name = Path(source).name or "repository"

        # Set default output filename if not provided
        if not output:
            output = f"{repo_name}.txt"

        # Parse command line patterns
        exclude_patterns = _parse_patterns(exclude_pattern)
        include_patterns = _parse_patterns(include_pattern)

        # Read and add patterns from ignore file
        ignore_file_path = Path(source) / ignore_file
        ignore_patterns = parse_ignore_file(ignore_file_path)
        exclude_patterns.update(ignore_patterns)

        # Perform the ingest operation with branch support
        summary, *_ = await ingest(source, max_size, include_patterns, exclude_patterns, branch=branch, output=output)

        # Display results
        click.echo(f"Analysis complete! Output written to: {output}")
        click.echo("\nSummary:")
        click.echo(summary)

    except FileNotFoundError as e:
        click.echo(f"Error: Source directory not found - {e}", err=True)
        raise click.Abort()
    except PermissionError as e:
        click.echo(f"Error: Permission denied - {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Warning: An error occurred - {e}", err=True)
        # For non-critical errors, we might want to continue rather than abort
        if isinstance(e, (OSError, IOError)):
            raise click.Abort()
        return


if __name__ == "__main__":
    main()
