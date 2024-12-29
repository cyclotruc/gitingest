import os
import pathlib

import click
import sys

from gitingest.ingest_from_query import MAX_FILE_SIZE
from .encoding import setup_encoding

# Setup encoding first
setup_encoding()

# Define constants
DEFAULT_IGNORE_PATTERNS = []

def normalize_pattern(pattern: str) -> str:
    pattern = pattern.strip()
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern


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
    """Analyze a directory and create a text dump of its contents."""
    try:
        from gitingest.ingest import ingest
        
        # Convert paths to absolute with proper encoding
        source = str(pathlib.Path(source).resolve())
        
        # Handle patterns
        exclude_patterns = list(exclude_pattern)
        include_patterns = list(set(include_pattern))
        
        # Set default output name
        if not output:
            output = "digest.txt"
        output = str(pathlib.Path(output).resolve())
        
        # Call ingest with encoding awareness
        summary, tree, content = ingest(
            source, 
            max_size, 
            include_patterns, 
            exclude_patterns, 
            output=output
        )
        
        # Write output with explicit encoding
        with open(output, 'w', encoding='utf-8', errors='replace') as f:
            if isinstance(summary, bytes):
                summary = summary.decode('utf-8', errors='replace')
            if isinstance(tree, bytes):
                tree = tree.decode('utf-8', errors='replace')
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='replace')
                
            f.write(f"{summary}\n\n{tree}\n\n{content}")
            
        # Print messages with encoding handling
        click.echo(f"Analysis complete! Output written to: {output}")
        click.echo("\nSummary:")
        click.echo(summary)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
