from typing import List, Union
import uuid
import os 


DEFAULT_IGNORE_PATTERNS = [
    # Python
    '*.pyc', '*.pyo', '*.pyd', '__pycache__', '.pytest_cache', '.coverage',
    '.tox', '.nox', '.mypy_cache', '.ruff_cache', '.hypothesis',
    'poetry.lock', 'Pipfile.lock',
    
    # JavaScript/Node
    'node_modules', 'bower_components', 'package-lock.json', 'yarn.lock',
    '.npm', '.yarn', '.pnpm-store',
    
    # Version control
    '.git', '.svn', '.hg', '.gitignore', '.gitattributes', '.gitmodules',
    
    # Images and media
    '*.svg', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.pdf',
    '*.mov', '*.mp4', '*.mp3', '*.wav',
    
    # Virtual environments
    'venv', '.venv', 'env', '.env', 'virtualenv',
    
    # IDEs and editors
    '.idea', '.vscode', '.vs', '*.swp', '*.swo', '*.swn',
    '.settings', '.project', '.classpath', '*.sublime-*',
    
    # Temporary and cache files
    '*.log', '*.bak', '*.swp', '*.tmp', '*.temp',
    '.cache', '.sass-cache', '.eslintcache',
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    
    # Build directories and artifacts
    'build', 'dist', 'target', 'out',
    '*.egg-info', '*.egg', '*.whl',
    '*.so', '*.dylib', '*.dll', '*.class',
    
    # Documentation
    'site-packages', '.docusaurus', '.next', '.nuxt',
    
    # Other common patterns
    '*.min.js', '*.min.css',  # Minified files
    '*.map',  # Source maps
    '.terraform', '*.tfstate*',  # Terraform
    'vendor/',  # Dependencies in various languages
]

TMP_BASE_PATH = "../tmp"

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
            raise ValueError(f"Pattern '{p}' contains invalid characters. Only alphanumeric characters, dash (-), underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed.")
    patterns = [normalize_pattern(p) for p in pattern.split(",")]
    return patterns

def override_ignore_patterns(ignore_patterns: List[str], include_patterns: List[str]) -> List[str]:
    for pattern in include_patterns:
        if pattern in ignore_patterns:
            ignore_patterns.remove(pattern)
    return ignore_patterns


def parse_path(path: str) -> dict:
    
    query = {
        "local_path": os.path.abspath(path),
        "slug": os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path),
        "subpath": "/",
        "id": str(uuid.uuid4()),
        "url": None,
    }
    return query

def parse_query(source: str, max_file_size: int, from_web: bool, include_patterns: Union[List[str], str] = None, ignore_patterns: Union[List[str], str] = None) -> dict:
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

def normalize_user_added_patterns(patterns: Union[List[str], str]) -> List[str]:
    if isinstance(patterns, str):
        patterns = patterns.split(',')
    return [normalize_pattern(pattern) for pattern in patterns]

def check_user_added_matches_suggestions(user_patterns: List[str], suggestions: List[str]) -> List[str]:
    normalized_user_patterns = normalize_user_added_patterns(user_patterns)
    return [pattern for pattern in normalized_user_patterns if pattern in suggestions]
