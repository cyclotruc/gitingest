from typing import List
from fastapi.templating import Jinja2Templates
from fastapi import Request

from config import MAX_DISPLAY_SIZE, EXAMPLE_REPOS
from gitingest import ingest_from_query, clone_repo, parse_query
from server_utils import logSliderToSize, Colors

templates = Jinja2Templates(directory="templates")

def print_query(query, request, max_file_size, pattern_type, pattern):
    print(f"{Colors.WHITE}{query['url']:<20}{Colors.END}", end="")
    if int(max_file_size/1024) != 50:
        print(f" | {Colors.YELLOW}Size: {int(max_file_size/1024)}kb{Colors.END}", end="")
    if pattern_type == "include" and pattern != "":
        print(f" | {Colors.YELLOW}Include {pattern}{Colors.END}", end="")
    elif pattern_type == "exclude" and pattern != "":
        print(f" | {Colors.YELLOW}Exclude {pattern}{Colors.END}", end="")


def print_error(query, request, e, max_file_size, pattern_type, pattern):
    print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
    print_query(query, request, max_file_size, pattern_type, pattern)
    print(f" | {Colors.RED}{e}{Colors.END}")

def print_success(query, request, max_file_size, pattern_type, pattern, summary):
    estimated_tokens = summary[summary.index("Estimated tokens:") + len("Estimated ") :]
    print(f"{Colors.GREEN}INFO{Colors.END}: {Colors.GREEN}<-  {Colors.END}", end="")
    print_query(query, request, max_file_size, pattern_type, pattern)
    print(f" | {Colors.PURPLE}{estimated_tokens}{Colors.END}")



async def process_query(request: Request, input_text: str, slider_position: int, pattern_type: str = "exclude", pattern: str = "", is_index: bool = False) -> str:
    template = "index.jinja" if is_index else "github.jinja"
    max_file_size = logSliderToSize(slider_position)
    if pattern_type == "include":
        include_patterns = pattern
        exclude_patterns = None
    elif pattern_type == "exclude":
        exclude_patterns = pattern
        include_patterns = None
    try:
        query = parse_query(input_text, max_file_size, True, include_patterns, exclude_patterns)
        await clone_repo(query)
        summary, tree, content = ingest_from_query(query)
        with open(f"{query['local_path']}.txt", "w") as f:
            f.write(tree + "\n" + content)

        
        
    except Exception as e:
        #hack to print error message when query is not defined
        if 'query' in locals() and query is not None and isinstance(query, dict):
                print_error(query, request, e, max_file_size, pattern_type, pattern)
        else:
            print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
            print(f"{Colors.RED}{e}{Colors.END}")
        return templates.TemplateResponse(
            template, 
            {
                "request": request,
                "github_url": input_text,
                "error_message": f"Error: {e}",
                "examples": EXAMPLE_REPOS if is_index else [],
                "default_file_size": slider_position,
                "pattern_type": pattern_type,
                "pattern": pattern,
            }
        )
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
    print_success(query, request, max_file_size, pattern_type, pattern, summary)
    return templates.TemplateResponse(
        template, 
        {
            "request": request, 
            "github_url": input_text,
            "result": True, 
            "summary": summary,
            "tree": tree, 
            "content": content,
            "examples": EXAMPLE_REPOS if is_index else [],
            "ingest_id": query['id'],
            "default_file_size": slider_position,
            "pattern_type": pattern_type,
            "pattern": pattern,
        }
    )
