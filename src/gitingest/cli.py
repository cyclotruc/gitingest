""" Command-line interface for the GitIngest package. """

# pylint: disable=no-value-for-parameter

import click

from gitingest.ingest import ingest
from gitingest.ingest_from_query import MAX_FILE_SIZE


@click.command()
@click.argument("source", type=str, required=True)
@click.option("--output", "-o", default=None, help="Output file path (default: <repo_name>.txt in current directory)")
@click.option("--max-size", "-s", default=MAX_FILE_SIZE, help="Maximum file size to process in bytes")
@click.option("--exclude-pattern", "-e", multiple=True, help="Patterns to exclude")
@click.option("--include-pattern", "-i", multiple=True, help="Patterns to include")
def main(
    source: str,
    output: str | None,
    max_size: int,
    exclude_pattern: tuple[str, ...],
    include_pattern: tuple[str, ...],
) -> None:
    """
    Analyze a directory or repository and create a text dump of its contents.

    This command analyzes the contents of a specified source directory or repository,
    applies custom include and exclude patterns, and generates a text summary of the analysis
    which is then written to an output file.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.
    output : str | None
        The path where the output file will be written. If not specified, the output will be written
        to a file named `<repo_name>.txt` in the current directory.
    max_size : int
        The maximum file size to process, in bytes. Files larger than this size will be ignored.
    exclude_pattern : tuple[str, ...]
        A tuple of patterns to exclude during the analysis. Files matching these patterns will be ignored.
    include_pattern : tuple[str, ...]
        A tuple of patterns to include during the analysis. Only files matching these patterns will be processed.

    Raises
    ------
    Abort
        If there is an error during the execution of the command, this exception is raised to abort the process.
    """
    try:
        # Combine default and custom ignore patterns
        exclude_patterns = list(exclude_pattern)
        include_patterns = list(set(include_pattern))

        if not output:
            output = "digest.txt"
        summary, _, _ = ingest(source, max_size, include_patterns, exclude_patterns, output=output)

        click.echo(f"Analysis complete! Output written to: {output}")
        click.echo("\nSummary:")
        click.echo(summary)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
