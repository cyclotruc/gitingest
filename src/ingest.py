import os
import fnmatch
from typing import Dict, List, Union
from config import DEFAULT_IGNORE_PATTERNS, MAX_FILE_SIZE, TMP_BASE_PATH

def should_ignore(path: str, base_path: str, ignore_patterns: List[str]) -> bool:
    """Checks if a file or directory should be ignored based on patterns."""
    name = os.path.basename(path)
    rel_path = os.path.relpath(path, base_path)
    
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern) or \
           fnmatch.fnmatch(rel_path, pattern):
            return True
    return False

def is_text_file(file_path: str) -> bool:
    """Determines if a file is likely a text file based on its content."""
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)
        return not bool(chunk.translate(None, bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))))
    except IOError:
        return False

def read_file_content(file_path: str) -> str:
    """Reads the content of a file, handling potential encoding errors."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
def analyze_directory(path: str, ignore_patterns: List[str], base_path: str) -> Dict:
    """Recursively analyzes a directory and its contents."""
    result = {
        "name": os.path.basename(path),
        "type": "directory",
        "size": 0,
        "children": [],
        "file_count": 0,
        "dir_count": 0,
        "path": path
    }

    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            
            if should_ignore(item_path, base_path, ignore_patterns):
                continue

            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                is_text = is_text_file(item_path)
                content = read_file_content(item_path) if is_text else "[Non-text file]"
                
                child = {
                    "name": item,
                    "type": "file",
                    "size": file_size,
                    "content": content,
                    "path": item_path
                }
                result["children"].append(child)
                result["size"] += file_size
                result["file_count"] += 1
                
            elif os.path.isdir(item_path):
                subdir = analyze_directory(item_path, ignore_patterns, base_path)
                if subdir:
                    result["children"].append(subdir)
                    result["size"] += subdir["size"]
                    result["file_count"] += subdir["file_count"]
                    result["dir_count"] += 1 + subdir["dir_count"]
                    
    except PermissionError:
        print(f"Permission denied: {path}")

    return result


def get_all_files(node: Dict, max_file_size: int, files: List = None) -> List[Dict]:
    """Recursively collects all text files with their contents."""
    if files is None:
        files = []
    
    if node["type"] == "file" and node["content"] != "[Non-text file]":
        content = node["content"]
        if node["size"] > max_file_size:
            content = "[Content ignored: file too large]"
            
        files.append({
            "path": node["path"].replace(TMP_BASE_PATH, ""),
            "content": content,
            "size": node["size"]
        })
    elif node["type"] == "directory":
        for child in node["children"]:
            get_all_files(child, max_file_size, files)
    return files

def create_file_content_string(files: List[Dict]) -> str:
    """Creates a formatted string of file contents with separators."""
    output = ""
    separator = "=" * 48 + "\n"
    
    for file in files:
        output += separator
        output += f"File: {file['path']}\n"
        output += separator
        output += f"{file['content']}\n\n"
    
    return output

def create_summary_string(result: Dict, files: List[Dict], query: dict) -> str:
    """Creates a summary string with file counts and content size."""
    total_lines = sum(len(file["content"].splitlines()) for file in files)
    
    return (
        f"Files analyzed: {result['file_count']}\n"
        f"Directories analyzed: {result['dir_count']}\n"
        f"Total lines of content: {total_lines:,}\n"
        f"branch: {query['branch'] if len(query['branch']) < 20 else query['branch'][:20] + '...'}\n"
        f"path: {query['subpath']}\n"
    )

def create_tree_structure(node: Dict, prefix: str = "", is_last: bool = True) -> str:
    """Creates a tree-like string representation of the file structure."""
    
    tree = ""
    current_prefix = "└── " if is_last else "├── "
    tree += prefix + current_prefix + node["name"] + "\n"
    
    if node["type"] == "directory":
        new_prefix = prefix + ("    " if is_last else "│   ")
        children = node["children"]
        for i, child in enumerate(children):
            tree += create_tree_structure(child, new_prefix, i == len(children) - 1)
    
    return tree


def ingest_from_path(query: dict, path: str, ignore_patterns: List[str] = DEFAULT_IGNORE_PATTERNS, max_file_size: int = MAX_FILE_SIZE, base_path: str = TMP_BASE_PATH) -> Dict:
    """Main entry point for analyzing a codebase directory."""
    
    path = f"{base_path}/{path}"
    if not os.path.exists(path):
        raise ValueError(f"Path {path} does not exist")
        
    
    nodes = analyze_directory(path, ignore_patterns, base_path)
    files = get_all_files(nodes, max_file_size)
    summary = create_summary_string(nodes, files, query)
    tree = "Directory structure:\n" + create_tree_structure(nodes)

    files_content = create_file_content_string(files)
    
    return (summary, tree, files_content)
