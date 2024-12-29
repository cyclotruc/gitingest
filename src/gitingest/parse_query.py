import os
import string
import sys
import uuid
from typing import Any, Union
from urllib.parse import urlparse, unquote

from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS

TMP_BASE_PATH = "../tmp"
HEX_DIGITS = set(string.hexdigits)


from urllib.parse import urlparse, unquote

def parse_url(url: str) -> dict[str, Any]:
    """Parse and validate a Git repository URL."""
    # Clean and decode URL
    url = unquote(url).strip()

    if not url.startswith("https://") and not url.startswith("http://"):
        url = "https://" + url

    # Parse the URL
    parsed_url = urlparse(url)

    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Invalid repository URL. Please provide a valid Git repository URL.")

    # Extract user and repository from path
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) < 2:
        raise ValueError("Invalid repository URL. Please provide a valid Git repository URL.")

    user_name = path_parts[0]
    repo_name = path_parts[1]
    _id = str(uuid.uuid4())
    slug = f"{user_name}-{repo_name}"

    parsed = {
        "user_name": user_name,
        "repo_name": repo_name,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": os.path.join(TMP_BASE_PATH, _id, slug),
        "url": f"{parsed_url.scheme}://{parsed_url.netloc}/{user_name}/{repo_name}",
        "slug": slug,
        "id": _id,
    }

    # Handle additional path components (tree/blob/commit)
    if len(path_parts) > 2 and path_parts[2] in ("issues", "pull"):
        return parsed

    if len(path_parts) >= 4:
        parsed["type"] = path_parts[2]  # Usually 'tree' or 'blob'
        commit_or_branch = path_parts[3]

        if _is_valid_git_commit_hash(commit_or_branch):
            parsed["commit"] = commit_or_branch
            if len(path_parts) > 4:
                parsed["subpath"] += "/".join(path_parts[4:])
        else:
            parsed["branch"] = commit_or_branch
            if len(path_parts) > 4:
                parsed["subpath"] += "/".join(path_parts[4:])

    return parsed


def _is_valid_git_commit_hash(commit: str) -> bool:
    """Check if a string is a valid Git commit hash."""
    return len(commit) == 40 and all(c in HEX_DIGITS for c in commit)


def normalize_pattern(pattern: str) -> str:
    """
    Normalize a pattern by stripping and formatting.

    Args:
        pattern (str): The ignore pattern.

    Returns:
        str: Normalized pattern.
    """
    pattern = pattern.strip()
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern


def parse_patterns(pattern: list[str] | str) -> list[str]:
    patterns = pattern if isinstance(pattern, list) else [pattern]
    patterns = [p.strip() for p in patterns]

    for p in patterns:
        if not all(c.isalnum() or c in "-_./+*" for c in p):
            raise ValueError(
                f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), "
                "underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed."
            )

    return [normalize_pattern(p) for p in patterns]


def override_ignore_patterns(ignore_patterns: list[str], include_patterns: list[str]) -> list[str]:
    """
    Removes patterns from ignore_patterns that are present in include_patterns using set difference.

    Parameters
    ----------
    ignore_patterns : List[str]
        The list of patterns to potentially remove.
    include_patterns : List[str]
        The list of patterns to exclude from ignore_patterns.

    Returns
    -------
    List[str]
        A new list of ignore_patterns with specified patterns removed.
    """
    return list(set(ignore_patterns) - set(include_patterns))

def extract_valid_url(source: str) -> Union[str, None]:
    """
    Extract and validate a valid URL from the given source.

    Args:
        source (str): The source string containing a potential URL.

    Returns:
        Union[str, None]: A valid URL if found, otherwise None.
    """
    # First, clean and unquote the source
    source = unquote(source).strip()
    
    # Direct match for full GitHub URLs
    github_match = re.match(r'^(https?://)?github\.com/[\w-]+/[\w-]+(/.*)?$', source.replace('\\', '/'))
    if github_match:
        # Ensure https:// prefix
        url = f"https://{github_match.group(0)}" if not source.startswith('http') else source
        print(f"\n🔧 Extracted GitHub URL: {url}")
        return url

    # Handle Windows-style paths that contain GitHub URL
    path_url_match = re.search(r'github\.com[/\\][\w-]+[/\\][\w-]+', source.replace('\\', '/'))
    if path_url_match:
        url = f"https://{path_url_match.group(0).replace('\\', '/')}"
        print(f"\n🔧 Extracted URL from path: {url}")
        return url

    # Fallback regex-based extraction
    match = re.search(r'https?://[^\s]+', source)
    if match:
        extracted_url = match.group(0)
        parsed_url = urlparse(extracted_url)
        if parsed_url.scheme and parsed_url.netloc:
            print(f"\n🔧 Extracted valid URL: {extracted_url}")
            return extracted_url

    return None

def parse_path(path: str) -> dict:
    """Parse a local file path."""
    # Normalize path separators and make absolute, remove trailing slashes
    normalized_path = os.path.abspath(os.path.normpath(path.rstrip('\\/')))
    
    return {
        "local_path": normalized_path,
        "slug": os.path.basename(normalized_path),
        "subpath": "/",
        "id": str(uuid.uuid4()),
        "url": None,
    }

import re

def parse_query(
    source: str,
    max_file_size: int,
    from_web: bool,
    include_patterns: Union[list[str], str] = None,
    ignore_patterns: Union[list[str], str] = None,
) -> dict[str, Any]:
    """Parse the query and apply ignore patterns."""
    
    # Step 1: Extract a valid URL 
    valid_url = extract_valid_url(source)
    
    if valid_url:
        print(f"\n🌐 Detected valid web URL: {valid_url}")
        is_web = True
        source = valid_url
    else:
        print(f"\n📂 Detected local path: {source}")
        is_web = from_web or source.startswith(('http://', 'https://')) or 'github.com' in source

    # Step 2: Handle Web URLs
    if is_web:
        print(f"\n🌐 Processing web URL: {source}")
        query = parse_url(source)
        query.update({
            "max_file_size": max_file_size,
            "ignore_patterns": DEFAULT_IGNORE_PATTERNS.copy(),
            "include_patterns": parse_patterns(include_patterns) if include_patterns else None
        })
        print(f"✅ Successfully parsed web URL: {query['url']}")
        return query

    # Step 3: Handle Local Paths
    source_path = os.path.abspath(os.path.normpath(source))
    query = {
        "local_path": source_path,
        "slug": os.path.basename(source_path),
        "subpath": "/",
        "id": str(uuid.uuid4()),
        "url": None,
    }

    final_ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()

    # Check .gitignore only for local paths
    gitignore_path = os.path.join(source_path, '.gitignore')
    print(f"\n🔍 Looking for .gitignore at: {gitignore_path}")
    
    if os.path.exists(gitignore_path):
        print(f"✅ Found .gitignore file")
        gitignore_patterns = parse_gitignore(gitignore_path)
        if gitignore_patterns:
            final_ignore_patterns.extend(gitignore_patterns)
            print("\n🔧 Added patterns from .gitignore")
    else:
        print("❌ No .gitignore file found")

    # Add user-defined ignore patterns
    if ignore_patterns:
        parsed_ignore = parse_patterns(ignore_patterns)
        final_ignore_patterns.extend(parsed_ignore)

    # Handle include patterns
    parsed_include = None
    if include_patterns:
        parsed_include = parse_patterns(include_patterns)
        final_ignore_patterns = override_ignore_patterns(final_ignore_patterns, parsed_include)

    # Update query
    query.update({
        "max_file_size": max_file_size,
        "ignore_patterns": final_ignore_patterns,
        "include_patterns": parsed_include,
    })

    return query









### 📝 **Parse .gitignore**
def parse_gitignore(gitignore_path: str) -> list[str]:
    """
    Parse .gitignore and return ignore patterns.
    """
    ignore_patterns = []
    print(f"\n📂 Attempting to read .gitignore from: {gitignore_path}")
    
    if not os.path.exists(gitignore_path):
        print(f"❌ .gitignore not found at: {gitignore_path}")
        return ignore_patterns

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as file:
            print("✅ Successfully opened .gitignore")
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    print(f"📌 Processing line: {line}")
                    if line.endswith('/'):
                        # For directory patterns (like logs/, backup/, etc)
                        base = line.rstrip('/')
                        patterns = [
                            f"{base}",  # Match directory itself
                            f"{base}/**",  # Match all contents
                            f"**/{base}",  # Match directory in subdirectories
                            f"**/{base}/**"  # Match contents in subdirectories
                        ]
                        ignore_patterns.extend(patterns)
                    else:
                        # Handle file patterns
                        ignore_patterns.append(line)
                        if '.' not in line and not line.endswith('/'):
                            ignore_patterns.append(f"{line}/")
                            
    except Exception as e:
        print(f"❌ Error reading .gitignore: {str(e)}")
        return []

    # Remove duplicates while preserving order
    list_ignore_patterns = list(dict.fromkeys(ignore_patterns))
    print("\n📋 Parsed ignore patterns from .gitignore:")
    for pattern in list_ignore_patterns:
        print(f"  - {pattern}")
    
    return list_ignore_patterns
