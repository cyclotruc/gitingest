import os
import pathlib
import click2

from gitingest.ingest import ingest
from gitingest.ingest_from_query import MAX_FILE_SIZE
from gitingest.parse_query import DEFAULT_IGNORE_PATTERNS

def normalize_pattern(pattern: str) -> str:
    pattern = pattern.strip()
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern

@click2.command()
@click2.argument('source', type=str, required=True)
@click2.option('--output', '-o', default=None, help='Output file path (default: <repo_name>.txt in current directory)')
@click2.option('--max-size', '-s', default=MAX_FILE_SIZE, help='Maximum file size to process in bytes')
@click2.option('--exclude-pattern', '-e', multiple=True, help='Patterns to exclude')
@click2.option('--include-pattern', '-i', multiple=True, help='Patterns to include')
def main(source, output, max_size, exclude_pattern, include_pattern):
    """Analyze a directory and create a text dump of its contents."""
    try:
        # Combine default and custom ignore patterns
        exclude_patterns = list(exclude_pattern)
        include_patterns = list(set(include_pattern))
        
        if not output:
            output = "digest.txt"
        summary, tree, content = ingest(source, max_size, include_patterns, exclude_patterns, output=output)
            
        click2.echo(f"Analysis complete! Output written to: {output}")
        click2.echo("\nSummary:")
        click2.echo(summary)
        
    except Exception as e:
        click2.echo(f"Error: {str(e)}", err=True)
        raise click2.Abort()

if __name__ == '__main__':
    main() 