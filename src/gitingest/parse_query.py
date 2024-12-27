import os
import uuid
from typing import Any, Dict, List, Optional, Union

from gitingest.ignore_patterns import DEFAULT_IGNORE_PATTERNS

TMP_BASE_PATH = "../tmp"


def parse_url(url: str) -> Dict[str, Any]:
    parsed = {
        "user_name": None,
        "repo_name": None,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": None,
        "url": None,
        "slug": None,
        "id": None,
    }

    url = url.split(" ")[0]
    if not url.startswith('https://'):
        url = 'https://' + url

    # Extract domain and path
    url_parts = url.split('/')
    domain = url_parts[2]
    path_parts = url_parts[3:]

    if len(path_parts) < 2:
        raise ValueError("Invalid repository URL. Please provide a valid Git repository URL.")

    parsed["user_name"] = path_parts[0]
    parsed["repo_name"] = path_parts[1]

    # Keep original URL format
    parsed["url"] = f"https://{domain}/{parsed['user_name']}/{parsed['repo_name']}"
    parsed['slug'] = f"{parsed['user_name']}-{parsed['repo_name']}"
    parsed["id"] = str(uuid.uuid4())
    parsed["local_path"] = f"{TMP_BASE_PATH}/{parsed['id']}/{parsed['slug']}"

    if len(path_parts) > 3:
        parsed["type"] = path_parts[2]
        parsed["branch"] = path_parts[3]
        if len(parsed['branch']) == 40 and all(c in '0123456789abcdefABCDEF' for c in parsed['branch']):
            parsed["commit"] = parsed['branch']

        parsed["subpath"] = "/" + "/".join(path_parts[4:])

    return parsed


def normalize_pattern(pattern: str) -> str:
    pattern = pattern.strip()
    pattern = pattern.lstrip(os.sep)
    if pattern.endswith(os.sep):
        pattern += "*"
    return pattern


def parse_patterns(pattern: Union[List[str], str]) -> List[str]:
    if isinstance(pattern, list):
        pattern = ",".join(pattern)

    for p in pattern.split(","):
        if not all(c.isalnum() or c in "-_./+*" for c in p.strip()):
            raise ValueError(
                f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), "
                "underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed."
            )
    patterns = [normalize_pattern(p) for p in pattern.split(",")]
    return patterns


def override_ignore_patterns(ignore_patterns: List[str], include_patterns: List[str]) -> List[str]:
    for pattern in include_patterns:
        if pattern in ignore_patterns:
            ignore_patterns.remove(pattern)
    return ignore_patterns


def parse_path(path: str) -> Dict[str, Any]:
    query = {
        "local_path": os.path.abspath(path),
        "slug": os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path),
        "subpath": "/",
        "id": str(uuid.uuid4()),
        "url": None,
    }
    return query


def parse_query(
    source: str,
    max_file_size: int,
    from_web: bool,
    include_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
) -> Dict[str, Any]:
    if from_web:
        query = parse_url(source)
    else:
        if source.startswith("https://") or "github.com" in source:
            query = parse_url(source)
        else:
            query = parse_path(source)

    query['max_file_size'] = max_file_size

    if ignore_patterns and ignore_patterns != "":
        ignore_patterns = DEFAULT_IGNORE_PATTERNS + parse_patterns(ignore_patterns)
    else:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS

    if include_patterns and include_patterns != "":
        include_patterns = parse_patterns(include_patterns)
        ignore_patterns = override_ignore_patterns(ignore_patterns, include_patterns)
    else:
        include_patterns = None

    query['ignore_patterns'] = ignore_patterns
    query['include_patterns'] = include_patterns

    return query
