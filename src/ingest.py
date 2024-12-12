import os
import fnmatch
from config import DEFAULT_IGNORE_PATTERNS, MAX_FILE_SIZE
from tokencost import count_string_tokens
from typing import Dict, List, Union

MAX_DIRECTORY_DEPTH = 10  # Maximum depth of directory traversal
MAX_FILES = 10000  # Maximum number of files to process
MAX_TOTAL_SIZE_BYTES = 100 * 1024 * 1024  # 100MB total size limit

def should_ignore(path: str, base_path: str, ignore_patterns: List[str]) -> bool:
    """Checks if a file or directory should be ignored based on patterns."""
    name = os.path.basename(path)
    rel_path = os.path.relpath(path, base_path)
    
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern) or \
           fnmatch.fnmatch(rel_path, pattern):
            return True
    return False

def is_safe_symlink(symlink_path: str, base_path: str) -> bool:
    """Check if a symlink points to a location within the base directory."""
    try:
        # Get the absolute path of the symlink target
        target_path = os.path.realpath(symlink_path)
        # Get the absolute path of the base directory
        base_path = os.path.realpath(base_path)
        # Check if the target path starts with the base path
        return os.path.commonpath([target_path]) == os.path.commonpath([target_path, base_path])
    except (OSError, ValueError):
        # If there's any error resolving the paths, consider it unsafe
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
    
def scan_directory(path: str, ignore_patterns: List[str], base_path: str, seen_paths: set = None, depth: int = 0, stats: Dict = None) -> Dict:
    """Recursively analyzes a directory and its contents with safety limits."""
    if seen_paths is None:
        seen_paths = set()
    if stats is None:
        stats = {"total_files": 0, "total_size": 0}
        
    # Check depth limit
    if depth > MAX_DIRECTORY_DEPTH:
        print(f"Skipping deep directory: {path} (max depth {MAX_DIRECTORY_DEPTH} reached)")
        return None
        
    # Check total files limit
    if stats["total_files"] >= MAX_FILES:
        print(f"Skipping further processing: maximum file limit ({MAX_FILES}) reached")
        return None
        
    # Check total size limit
    if stats["total_size"] >= MAX_TOTAL_SIZE_BYTES:
        print(f"Skipping further processing: maximum total size ({MAX_TOTAL_SIZE_BYTES/1024/1024:.1f}MB) reached")
        return None
        
    real_path = os.path.realpath(path)
    if real_path in seen_paths:
        print(f"Skipping already visited path: {path}")
        return None
    seen_paths.add(real_path)
    
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

            # Handle symlinks
            if os.path.islink(item_path):
                if not is_safe_symlink(item_path, base_path):
                    print(f"Skipping symlink that points outside base directory: {item_path}")
                    continue
                real_path = os.path.realpath(item_path)
                if real_path in seen_paths:
                    print(f"Skipping already visited symlink target: {item_path}")
                    continue
                
                if os.path.isfile(real_path):
                    file_size = os.path.getsize(real_path)
                    # Check if adding this file would exceed total size limit
                    if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
                        print(f"Skipping file {item_path}: would exceed total size limit")
                        continue
                        
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    if stats["total_files"] > MAX_FILES:
                        print(f"Maximum file limit ({MAX_FILES}) reached")
                        return result
                        
                    is_text = is_text_file(real_path)
                    content = read_file_content(real_path) if is_text else "[Non-text file]"
                    
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
                    
                elif os.path.isdir(real_path):
                    subdir = scan_directory(real_path, ignore_patterns, base_path, seen_paths, depth + 1, stats)
                    if subdir:
                        subdir["name"] = item
                        subdir["path"] = item_path
                        result["children"].append(subdir)
                        result["size"] += subdir["size"]
                        result["file_count"] += subdir["file_count"]
                        result["dir_count"] += 1 + subdir["dir_count"]
                continue

            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                # Check if adding this file would exceed total size limit
                if stats["total_size"] + file_size > MAX_TOTAL_SIZE_BYTES:
                    print(f"Skipping file {item_path}: would exceed total size limit")
                    continue
                    
                stats["total_files"] += 1
                stats["total_size"] += file_size
                
                if stats["total_files"] > MAX_FILES:
                    print(f"Maximum file limit ({MAX_FILES}) reached")
                    return result
                    
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
                subdir = scan_directory(item_path, ignore_patterns, base_path, seen_paths, depth + 1, stats)
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

    summary = f"Repository: {query['user_name']}/{query['repo_name']}\n"
    summary += f"Files analyzed: {nodes['file_count']}\n"
    
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

def generate_token_string(context_string: str) -> str:
    formatted_tokens = ""
    try: 
        total_gpt_tokens = count_string_tokens(prompt=context_string, model="gpt-4o")
    except Exception as e:
        return None
    if total_gpt_tokens > 1000000:  
            formatted_tokens = f"{total_gpt_tokens/1000000:.1f}M"
    elif total_gpt_tokens > 1000:
        formatted_tokens = f"{total_gpt_tokens/1000:.1f}k"
    else:
        formatted_tokens = f"{total_gpt_tokens}"
    return formatted_tokens

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


        print(files_content)
        formatted_tokens = generate_token_string(files_content)
        if formatted_tokens:
            summary += f"\nEstimated tokens: {formatted_tokens}"
        return (summary, tree, files_content)
    
    else:
        nodes = scan_directory(path, ignore_patterns, query['local_path'])
        files = extract_files_content(query, nodes, max_file_size)
        summary = create_summary_string(query, nodes, files)
        tree = "Directory structure:\n" + create_tree_structure(query, nodes)
        files_content = create_file_content_string(files)


        formatted_tokens = generate_token_string(tree + files_content)
        if formatted_tokens:
            summary += f"\nEstimated tokens: {formatted_tokens}"
        
        



    
    return (summary, tree, files_content)
