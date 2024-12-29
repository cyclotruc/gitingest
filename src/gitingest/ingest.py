import asyncio
import inspect
import shutil
from pathlib import Path
import io
import sys
from typing import Union

# Import other modules from the package
from gitingest.parse_query import parse_query
from gitingest.clone import clone_repo, CloneConfig
from gitingest.ingest_from_query import ingest_from_query

def setup_encoding():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def ingest(source: str, max_file_size: int = 10 * 1024 * 1024, 
          include_patterns: Union[list[str], str] = None, 
          exclude_patterns: Union[list[str], str] = None, 
          output: str = None) -> tuple[str, str, str]:
    """
    Analyze and create a text dump of source contents.
    
    Args:
        source: Path to source directory or git URL
        max_file_size: Maximum file size to process in bytes
        include_patterns: Patterns to include in analysis
        exclude_patterns: Patterns to exclude from analysis
        output: Output file path
    
    Returns:
        Tuple of (summary, tree, content)
    """
    setup_encoding()
    query = None
    
    try:
        query = parse_query(
            source=source,
            max_file_size=max_file_size,
            from_web=False,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
        )
        if query["url"]:

            # Extract relevant fields for CloneConfig
            clone_config = CloneConfig(
                url=query["url"],
                local_path=query["local_path"],
                commit=query.get("commit"),
                branch=query.get("branch"),
            )
            clone_result = clone_repo(clone_config)

            if inspect.iscoroutine(clone_result):
                asyncio.run(clone_result)
            else:
                raise TypeError("clone_repo did not return a coroutine as expected.")

        summary, tree, content = ingest_from_query(query)

        if output:
            # Write with explicit UTF-8 encoding
            with open(output, "w", encoding='utf-8', errors='replace') as f:
                # Ensure all content is properly encoded
                tree = tree.encode('utf-8', errors='replace').decode('utf-8') if isinstance(tree, str) else tree
                content = content.encode('utf-8', errors='replace').decode('utf-8') if isinstance(content, str) else content
                f.write(f"{tree}\n{content}")

        return summary, tree, content
        
    except UnicodeEncodeError as e:
        # Handle encoding errors specifically
        error_msg = f"Encoding error while processing {source}: {str(e)}"
        raise RuntimeError(error_msg)
        
    except Exception as e:
        # Handle other errors
        error_msg = f"Error while processing {source}: {str(e)}"
        raise RuntimeError(error_msg)
        
    finally:
        # Clean up the temporary directory if it was created
        if query and query.get('url'):
            # Get parent directory two levels up from local_path (../tmp)
            cleanup_path = str(Path(query['local_path']).parents[1])
            try:
                shutil.rmtree(cleanup_path, ignore_errors=True)
            except Exception as e:
                print(f"Warning: Could not clean up temporary directory: {str(e)}", file=sys.stderr)