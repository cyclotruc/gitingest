""" Process a query by parsing input, cloning a repository, and generating a summary. """

import os
from functools import partial

from fastapi import Request
from starlette.templating import _TemplateResponse

from gitingest.query_ingestion import run_ingest_query
from gitingest.query_parser import ParsedQuery, parse_query
from gitingest.repository_clone import CloneConfig, clone_repo
from server.server_config import EXAMPLE_REPOS, MAX_DISPLAY_SIZE, templates
from server.server_utils import Colors, log_slider_to_size


async def process_query(
    request: Request,
    input_text: str,
    slider_position: int,
    pattern_type: str = "exclude",
    pattern: str = "",
    is_index: bool = False,
) -> _TemplateResponse:
    """
    Process a query by parsing input, cloning a repository, and generating a summary.

    Handle user input, process Git repository data, and prepare
    a response for rendering a template with the processed results or an error message.

    Parameters
    ----------
    request : Request
        The HTTP request object.
    input_text : str
        Input text provided by the user, typically a Git repository URL or slug.
    slider_position : int
        Position of the slider, representing the maximum file size in the query.
    pattern_type : str
        Type of pattern to use, either "include" or "exclude" (default is "exclude").
    pattern : str
        Pattern to include or exclude in the query, depending on the pattern type.
    is_index : bool
        Flag indicating whether the request is for the index page (default is False).

    Returns
    -------
    _TemplateResponse
        Rendered template response containing the processed results or an error message.

    """
    include_patterns, exclude_patterns = validate_pattern_type(pattern_type, pattern)
    template = "index.jinja" if is_index else "git.jinja"
    template_response = partial(templates.TemplateResponse, name=template)
    max_file_size = log_slider_to_size(slider_position)

    context = create_context(request, input_text, slider_position, pattern_type, pattern, is_index)

    try:
        parsed_query = await parse_query(
            source=input_text,
            max_file_size=max_file_size,
            from_web=True,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
        )
        validate_parsed_query(parsed_query)

        clone_config = CloneConfig(
            url=parsed_query.url,
            local_path=str(parsed_query.local_path),
            commit=parsed_query.commit,
            branch=parsed_query.branch,
        )
        await clone_repo(clone_config)

        update_ignore_patterns(parsed_query, clone_config.local_path)

        summary, tree, content = run_ingest_query(parsed_query)
        save_ingest_result(clone_config.local_path, tree, content)
        content = filter_ignored_files(parsed_query, content)

    except Exception as e:
        handle_query_error(e, parsed_query, max_file_size, pattern_type, pattern, context)
        return template_response(context=context)

    content = truncate_content(content)

    _print_success(
        url=parsed_query.url,
        max_file_size=max_file_size,
        pattern_type=pattern_type,
        pattern=pattern,
        summary=summary,
    )

    context.update(
        {
            "result": True,
            "summary": summary,
            "tree": tree,
            "content": content,
            "ingest_id": parsed_query.id,
        }
    )

    return template_response(context=context)


def validate_pattern_type(pattern_type: str, pattern: str):
    """
    Ensure valid pattern type and return the corresponding include/exclude patterns.

    Parameters
    ----------
    pattern_type : str
        Specifies the type of pattern, either "include" or "exclude".
    pattern : str
        The pattern string to be included or excluded.

    Returns
    -------
    tuple
        A tuple containing either the include or exclude pattern.

    Raises
    ------
    ValueError
        If an invalid pattern type is provided.
    """
    if pattern_type == "include":
        return pattern, None
    if pattern_type == "exclude":
        return None, pattern
    raise ValueError(f"Invalid pattern type: {pattern_type}")


def create_context(
    request: Request, input_text: str, slider_position: int, pattern_type: str, pattern: str, is_index: bool
) -> dict:
    """
    Prepare the context dictionary for rendering templates.

    Parameters
    ----------
    request : Request
        The HTTP request object.
    input_text : str
        The user-provided input text (Git repository URL or slug).
    slider_position : int
        The position of the slider, representing the maximum file size in the query.
    pattern_type : str
        Type of pattern to use, either "include" or "exclude".
    pattern : str
        The pattern string to include or exclude.
    is_index : bool
        Boolean flag indicating if the request is for the index page.

    Returns
    -------
    dict
        A dictionary containing template context data.
    """
    return {
        "request": request,
        "repo_url": input_text,
        "examples": EXAMPLE_REPOS if is_index else [],
        "default_file_size": slider_position,
        "pattern_type": pattern_type,
        "pattern": pattern,
    }


def validate_parsed_query(parsed_query: ParsedQuery):
    """
    Check if the parsed query contains a valid URL.

    Parameters
    ----------
    parsed_query : ParsedQuery
        The parsed query object containing repository information.

    Raises
    ------
    ValueError
        If the URL parameter is missing in the parsed query.
    """
    if not parsed_query.url:
        raise ValueError("The 'url' parameter is required.")


def update_ignore_patterns(parsed_query: ParsedQuery, local_path: str):
    """
    Load ignore patterns from `.gitingestignore` file if present.

    Parameters
    ----------
    parsed_query : ParsedQuery
        The parsed query object containing repository details.
    local_path : str
        The local path where the repository is cloned.
    """
    ignore_file_path = os.path.join(local_path, ".gitingestignore")
    if os.path.exists(ignore_file_path):
        with open(ignore_file_path, encoding="utf-8") as ignore_file:
            additional_ignore_patterns = [
                line.strip() for line in ignore_file if line.strip() and not line.startswith("#")
            ]

        if additional_ignore_patterns:
            parsed_query.ignore_patterns = parsed_query.ignore_patterns or set()
            parsed_query.ignore_patterns.update(additional_ignore_patterns)


def save_ingest_result(local_path: str, tree: str, content: str):
    """
    Save the repository tree and file content to a text file.

    Parameters
    ----------
    local_path : str
        The local path where the repository is cloned.
    tree : str
        The repository tree structure.
    content : str
        The ingested file content.
    """
    with open(f"{local_path}.txt", "w", encoding="utf-8") as f:
        f.write(tree + "\n" + content)


def filter_ignored_files(parsed_query: ParsedQuery, content: str) -> str:
    """
    Remove ignored file patterns from content.

    Parameters
    ----------
    parsed_query : ParsedQuery
        The parsed query object containing ignore patterns.
    content : str
        The content to be filtered.

    Returns
    -------
    str
        The filtered content without ignored patterns.
    """
    if parsed_query.ignore_patterns:
        content = "\n".join(
            line
            for line in content.splitlines()
            if not any(ignored in line for ignored in parsed_query.ignore_patterns)
        )
    return content


def handle_query_error(
    e: Exception, parsed_query: ParsedQuery, max_file_size: int, pattern_type: str, pattern: str, context: dict
):
    """
    Handle exceptions during query processing and log errors.

    Parameters
    ----------
    e : Exception
        The exception raised during processing.
    parsed_query : ParsedQuery
        The parsed query object.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern used.
    pattern : str
        The actual pattern string used.
    context : dict
        The template context dictionary.
    """
    if "query" in locals() and parsed_query is not None and isinstance(parsed_query, dict):
        _print_error(parsed_query["url"], e, max_file_size, pattern_type, pattern)
    else:
        print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}{Colors.RED}{e}{Colors.END}")

    context["error_message"] = f"Error: {e}"


def truncate_content(content: str) -> str:
    """
    Truncate content if it exceeds the maximum display size.

    Parameters
    ----------
    content : str
        The content to be truncated.

    Returns
    -------
    str
        The truncated content, if applicable.
    """
    if len(content) > MAX_DISPLAY_SIZE:
        content = (
            f"(Files content cropped to {int(MAX_DISPLAY_SIZE / 1_000)}k characters, "
            "download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        )
    return content


def _print_query(url: str, max_file_size: int, pattern_type: str, pattern: str) -> None:
    """
    Print a formatted summary of the query details.

    Parameters
    ----------
    url : str
        The URL associated with the query.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern to use, either "include" or "exclude".
    pattern : str
        The actual pattern string to include or exclude in the query.
    """
    print(f"{Colors.WHITE}{url:<20}{Colors.END}", end="")
    if int(max_file_size / 1024) != 50:
        print(f" | {Colors.YELLOW}Size: {int(max_file_size/1024)}kb{Colors.END}", end="")
    if pattern_type == "include" and pattern:
        print(f" | {Colors.YELLOW}Include {pattern}{Colors.END}", end="")
    elif pattern_type == "exclude" and pattern:
        print(f" | {Colors.YELLOW}Exclude {pattern}{Colors.END}", end="")
    print()


def _print_error(url: str, e: Exception, max_file_size: int, pattern_type: str, pattern: str) -> None:
    """
    Print a formatted error message including details of the exception.

    Parameters
    ----------
    url : str
        The URL associated with the query that caused the error.
    e : Exception
        The exception raised during the query or process.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern to use, either "include" or "exclude".
    pattern : str
        The actual pattern string to include or exclude in the query.
    """
    print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
    _print_query(url, max_file_size, pattern_type, pattern)
    print(f" | {Colors.RED}{e}{Colors.END}")


def _print_success(url: str, max_file_size: int, pattern_type: str, pattern: str, summary: str) -> None:
    """
    Print a formatted success message, including estimated tokens.

    Parameters
    ----------
    url : str
        The URL associated with the successful query.
    max_file_size : int
        The maximum file size allowed for the query, in bytes.
    pattern_type : str
        Specifies the type of pattern to use, either "include" or "exclude".
    pattern : str
        The actual pattern string to include or exclude in the query.
    summary : str
        A summary of the query result, including details like estimated tokens.
    """
    estimated_tokens = summary[summary.index("Estimated tokens:") + len("Estimated ") :]
    print(f"{Colors.GREEN}INFO{Colors.END}: {Colors.GREEN}<-  {Colors.END}", end="")
    _print_query(url, max_file_size, pattern_type, pattern)
    print(f" | {Colors.PURPLE}{estimated_tokens}{Colors.END}")
