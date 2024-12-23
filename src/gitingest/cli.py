import os
import pathlib
import click

from gitingest.ingest import ingest
from gitingest.ingest_from_query import MAX_FILE_SIZE, generate_suggestions, check_relevance, sort_suggestions
from gitingest.parse_query import DEFAULT_IGNORE_PATTERNS

def normalize_pattern(pattern: str) -> str:
    pattern = pattern.strip()
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern

@click.command()
@click.argument('source', type=str, required=True)
@click.option('--output', '-o', default=None, help='Output file path (default: <repo_name>.txt in current directory)')
@click.option('--max-size', '-s', default=MAX_FILE_SIZE, help='Maximum file size to process in bytes')
@click.option('--exclude-pattern', '-e', multiple=True, help='Patterns to exclude')
@click.option('--include-pattern', '-i', multiple=True, help='Patterns to include')
@click.option('--suggestions', is_flag=True, help='Display quick suggestions for include/exclude patterns')
def main(source, output, max_size, exclude_pattern, include_pattern, suggestions):
    """Analyze a directory and create a text dump of its contents."""
    try:
        # Combine default and custom ignore patterns
        exclude_patterns = list(exclude_pattern)
        include_patterns = list(set(include_pattern))
        
        if suggestions:
            query = {
                'local_path': source,
                'include_patterns': include_patterns,
                'ignore_patterns': exclude_patterns
            }
            suggestions_list = generate_suggestions(query)
            relevant_suggestions = [s for s in suggestions_list if check_relevance(query, s)]
            sorted_suggestions = sort_suggestions(query, relevant_suggestions)
            click.echo("Quick Suggestions:")
            for suggestion in sorted_suggestions[:5]:
                click.echo(f"- {suggestion}")
            return
        
        if not output:
            output = "digest.txt"
        summary, tree, content = ingest(source, max_size, include_patterns, exclude_patterns, output=output)
            
        click.echo(f"Analysis complete! Output written to: {output}")
        click.echo("\nSummary:")
        click.echo(summary)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main() 
