import os
import fnmatch
from typing import Dict, List, Union
from config import DEFAULT_IGNORE_PATTERNS, MAX_FILE_SIZE

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
    
def scan_directory(path: str, ignore_patterns: List[str], base_path: str) -> Dict:
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
                subdir = scan_directory(item_path, ignore_patterns, base_path)
                if subdir:
                    result["children"].append(subdir)
                    result["size"] += subdir["size"]
                    result["file_count"] += subdir["file_count"]
                    result["dir_count"] += 1 + subdir["dir_count"]
                    
    except PermissionError:
        print(f"Permission denied: {path}")

    return result


def extract_files_content(query: dict, node: Dict, max_file_size: int, files: List = None) -> List[Dict]:
    """Recursively collects all text files with their contents."""
    if files is None:
        files = []
    
    if node["type"] == "file" and node["content"] != "[Non-text file]":
        content = node["content"]
        if node["size"] > max_file_size:
            content = "[Content ignored: file too large]"
            
        files.append({
            "path": node["path"].replace(query['local_path'], ""),
            "content": content,
            "size": node["size"]
        })
    elif node["type"] == "directory":
        for child in node["children"]:
            extract_files_content(query, child, max_file_size, files)
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

def create_summary_string(query: dict, nodes: Dict, files: List[Dict], ) -> str:
    """Creates a summary string with file counts and content size."""
    total_lines = sum(len(file["content"].splitlines()) for file in files)

    summary = f"Repository: {query['user_name']}/{query['repo_name']}\n"
    summary += f"Files analyzed: {nodes['file_count']}\n"
    summary += f"Directories analyzed: {nodes['dir_count']}\n"
    summary += f"Total lines of content: {total_lines:,}\n"
    if query['subpath'] != '/':
        summary += f"Subpath: {query['subpath']}\n"
    if query['commit']:
        summary += f"Commit: {query['commit']}\n"
    elif query['branch'] != 'main' and query['branch'] != 'master' and query['branch']:
        summary += f"Branch: {query['branch']}\n"
    return summary
        


def create_tree_structure(query: dict, node: Dict, prefix: str = "", is_last: bool = True) -> str:
    """Creates a tree-like string representation of the file structure."""
    
    tree = ""
    # Only add the root node name if it's not an empty string
    if not node["name"]:
        node["name"] = query['slug']

    if node["name"]:
        current_prefix = "└── " if is_last else "├── "
        tree += prefix + current_prefix + node["name"] + "\n"
        
    if node["type"] == "directory":
        # Adjust prefix only if we added a node name
        new_prefix = prefix + ("    " if is_last else "│   ") if node["name"] else prefix
        children = node["children"]
        for i, child in enumerate(children):
            tree += create_tree_structure(query, child, new_prefix, i == len(children) - 1)
    
    return tree


def ingest_from_query(query: dict, ignore_patterns: List[str] = DEFAULT_IGNORE_PATTERNS, max_file_size: int = MAX_FILE_SIZE) -> Dict:
    """Main entry point for analyzing a codebase directory or single file."""
    
    path = f"{query['local_path']}{query['subpath']}"
    if not os.path.exists(path):
        raise ValueError(f"{query['slug']} cannot be found, make sure the repository is public")
    
    if query.get('type') == 'blob':
        if not os.path.isfile(path):
            raise ValueError(f"Path {path} is not a file")
            
        file_size = os.path.getsize(path)
        is_text = is_text_file(path)
        if not is_text:
            raise ValueError(f"File {path} is not a text file")
            
        content = read_file_content(path)
        if file_size > max_file_size:
            content = "[Content ignored: file too large]"
            
        file_info = {
            "path": path.replace(query['local_path'], ""),
            "content": content,
            "size": file_size
        }
        
        summary = (
            f"Repository: {query['user_name']}/{query['repo_name']}\n"
            f"File: {os.path.basename(path)}\n"
            f"Size: {file_size:,} bytes\n"
            f"Lines: {len(content.splitlines()):,}\n"
        )
        
        files_content = create_file_content_string([file_info])
        tree = "Directory structure:\n└── " + os.path.basename(path)
        return (summary, tree, files_content)
    
    else:
        nodes = scan_directory(path, ignore_patterns, query['local_path'])
        files = extract_files_content(query, nodes, max_file_size)
        summary = create_summary_string(query, nodes, files)
        tree = "Directory structure:\n" + create_tree_structure(query, nodes)
        files_content = create_file_content_string(files)
    
    return (summary, tree, files_content)
