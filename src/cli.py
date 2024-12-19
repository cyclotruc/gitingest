import click
import os
from .ingest import analyze_codebase, DEFAULT_IGNORE_PATTERNS, MAX_FILE_SIZE

@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', default=None, help='Output file path (default: <repo_name>.txt in current directory)')
@click.option('--max-size', '-s', default=MAX_FILE_SIZE, help='Maximum file size to process in bytes')
@click.option('--ignore-pattern', '-i', multiple=True, help='Additional patterns to ignore')
def main(path, output, max_size, ignore_pattern):
    """Analyze a directory and create a text dump of its contents."""
    try:
        # Convert path to absolute path
        abs_path = os.path.abspath(path)
        repo_name = os.path.basename(abs_path)
        
        # Combine default and custom ignore patterns
        ignore_patterns = list(DEFAULT_IGNORE_PATTERNS)
        if ignore_pattern:
            ignore_patterns.extend(ignore_pattern)
            
        # If no output file specified, use repo name in current directory
        if output is None:
            output = f"{repo_name}.txt"
            
        # Create a query dict to match the expected format
        query = {
            'local_path': abs_path,
            'subpath': '/',
            'user_name': os.path.basename(os.path.dirname(abs_path)),
            'repo_name': repo_name,
            'ignore_patterns': ignore_patterns,
            'include_patterns': [],
            'pattern_type': 'exclude',
            'max_file_size': max_size,
            'branch': None,
            'commit': None,
            'type': 'tree',
            'slug': repo_name
        }
            
        # Run analysis
        summary, tree, content = analyze_codebase(query)
        
        # Write to file
        with open(output, 'w') as f:
            f.write(f"Summary:\n{summary}\n\n")
            f.write(f"{tree}\n")
            f.write(content)
            
        click.echo(f"Analysis complete! Output written to: {output}")
        click.echo("\nSummary:")
        click.echo(summary)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main() 