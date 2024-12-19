import uuid
import re
import os 
from utils.log_convert import logSliderToSize
from typing import List

from config import TMP_BASE_PATH, DEFAULT_IGNORE_PATTERNS

def parse_url(url: str) -> dict:
    parsed = {
        "user_name": None,
        "repo_name": None,
        "type": None,
        "branch": None,
        "commit": None,
        "subpath": "/",
        "local_path": None,
        "url": None,
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

def parse_patterns(pattern: str) -> List[str]:
    for p in pattern.split(","):
        if not all(c.isalnum() or c in "-_./+*" for c in p.strip()):
            raise ValueError(f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed.")
    
    patterns = [normalize_pattern(p) for p in pattern.split(",")]
    if len(patterns) >= 10:
        raise ValueError("Maximum of 10 patterns allowed")
    return patterns

def override_ignore_patterns(ignore_patterns: List[str], include_patterns: List[str]) -> List[str]:
    for pattern in include_patterns:
        if pattern in ignore_patterns:
            ignore_patterns.remove(pattern)
    return ignore_patterns

def parse_query(input_text: str, slider_position: int, pattern_type: str, pattern: str) -> dict:
    query = parse_url(input_text)
    query['max_file_size'] = logSliderToSize(slider_position)
    query['pattern_type'] = pattern_type
    parsed_pattern = parse_patterns(pattern)
    if pattern_type == 'include':
        query['include_patterns'] = parsed_pattern
        query['ignore_patterns'] = override_ignore_patterns(DEFAULT_IGNORE_PATTERNS, parsed_pattern)
    else:
        query['ignore_patterns'] = DEFAULT_IGNORE_PATTERNS.copy()
        query['ignore_patterns'].extend(parsed_pattern)
        query['include_patterns'] = None

    print(f"{query['slug']:<20} | {query['pattern_type']}[{pattern}] {int(query['max_file_size']/1024)}kb, \n{query['url']}")
    return query

