"""Process a query by parsing input, cloning a repository, and generating a summary."""

from functools import partial
from typing import Optional

from fastapi import Request
from starlette.templating import _TemplateResponse

from gitingest.cloning import clone_repo
from gitingest.ingestion import ingest_query
from gitingest.query_parsing import IngestionQuery, parse_query
from server.server_config import EXAMPLE_REPOS, MAX_DISPLAY_SIZE, templates
from server.server_utils import Colors, log_slider_to_size


async def process_query(
    request: Request,
    input_text: str,
    slider_position: int,
    pattern_type: str = "exclude",
    pattern: str = "",
    is_index: bool = False,
    access_token: Optional[str] = None,
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
    access_token : str, optional
        Access token for private repositories (optional).

    Returns
    -------
    _TemplateResponse
        Rendered template response containing the processed results or an error message.

    Raises
    ------
    ValueError
        If an invalid pattern type is provided.
    """
    if pattern_type == "include":
        include_patterns = pattern
        exclude_patterns = None
    elif pattern_type == "exclude":
        exclude_patterns = pattern
        include_patterns = None
    else:
        raise ValueError(f"Invalid pattern type: {pattern_type}")

    template = "index.jinja" if is_index else "git.jinja"
    template_response = partial(templates.TemplateResponse, name=template)
    max_file_size = log_slider_to_size(slider_position)

    context = {
        "request": request,
        "repo_url": input_text,
        "examples": EXAMPLE_REPOS if is_index else [],
        "default_file_size": slider_position,
        "pattern_type": pattern_type,
        "pattern": pattern,
    }

    try:
        query: IngestionQuery = await parse_query(
            source=input_text,
            max_file_size=max_file_size,
            from_web=True,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
        )
        if not query.url:
            raise ValueError("The 'url' parameter is required.")

        clone_config = query.extract_clone_config()
        await clone_repo(clone_config, access_token=access_token)
        summary, tree, content = ingest_query(query)
        with open(f"{clone_config.local_path}.txt", "w", encoding="utf-8") as f:
            f.write(tree + "\n" + content)
    except Exception as exc:
        # hack to print error message when query is not defined
        if "query" in locals() and query is not None and isinstance(query, dict):
            _print_error(query["url"], exc, max_file_size, pattern_type, pattern, access_token)
        else:
            print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
            print(f"{Colors.RED}{exc}{Colors.END}")

        error_message = str(exc)
        user_facing_error = f"An unexpected error occurred: {error_message}" # Default

        # Check for specific, common errors to provide better messages
        if isinstance(exc, ValueError) and "Repository not found or inaccessible" in error_message:
            user_facing_error = error_message # Use the specific message from cloning.py
        elif isinstance(exc, RuntimeError) and "Authentication failed" in error_message:
            user_facing_error = "Authentication failed. Please check your token and repository permissions."
        elif isinstance(exc, RuntimeError) and "could not read Username" in error_message:
             user_facing_error = "Authentication failed. Please check your token and repository permissions."
        elif isinstance(exc, TimeoutError) or "timed out" in error_message:
             user_facing_error = "Cloning timed out. The repository might be too large or the network slow."
        elif isinstance(exc, ValueError) and "Invalid repository URL" in error_message:
            user_facing_error = "Invalid repository URL format."
        elif isinstance(exc, FileNotFoundError):
            user_facing_error = "Ingestion failed: Cloned repository directory not found."

        context["error_message"] = user_facing_error
        return template_response(context=context)

    if len(content) > MAX_DISPLAY_SIZE:
        content = (
            f"(Files content cropped to {int(MAX_DISPLAY_SIZE / 1_000)}k characters, "
            "download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        )

    _print_success(
        url=query.url,
        max_file_size=max_file_size,
        pattern_type=pattern_type,
        pattern=pattern,
        summary=summary,
        access_token=access_token,
    )

    context.update(
        {
            "result": True,
            "summary": summary,
            "tree": tree,
            "content": content,
            "ingest_id": query.id,
        }
    )

    return template_response(context=context)


def _print_query(url: str, max_file_size: int, pattern_type: str, pattern: str, access_token: Optional[str] = None) -> None:
    """
    Print a formatted summary of the query details, including the URL, file size,
    and pattern information, for easier debugging or logging.

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
    access_token : str, optional
        Access token (NOT logged for security).
    """
    print(f"{Colors.WHITE}{url:<20}{Colors.END}", end="")
    if int(max_file_size / 1024) != 50:
        print(f" | {Colors.YELLOW}Size: {int(max_file_size/1024)}kb{Colors.END}", end="")
    if pattern_type == "include" and pattern != "":
        print(f" | {Colors.YELLOW}Include {pattern}{Colors.END}", end="")
    elif pattern_type == "exclude" and pattern != "":
        print(f" | {Colors.YELLOW}Exclude {pattern}{Colors.END}", end="")
    # Ensure token is never printed
    if access_token:
        print(f" | {Colors.YELLOW}Token: [REDACTED]{Colors.END}", end="")


def _print_error(url: str, e: Exception, max_file_size: int, pattern_type: str, pattern: str, access_token: Optional[str] = None) -> None:
    """
    Print a formatted error message including the URL, file size, pattern details, and the exception encountered,
    for debugging or logging purposes.

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
    access_token : str, optional
        Access token (NOT logged for security).
    """
    print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
    _print_query(url, max_file_size, pattern_type, pattern, access_token)
    print(f" | {Colors.RED}{e}{Colors.END}")


def _print_success(url: str, max_file_size: int, pattern_type: str, pattern: str, summary: str, access_token: Optional[str] = None) -> None:
    """
    Print a formatted success message, including the URL, file size, pattern details, and a summary with estimated
    tokens, for debugging or logging purposes.

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
    access_token : str, optional
        Access token (NOT logged for security).
    """
    estimated_tokens = summary[summary.index("Estimated tokens:") + len("Estimated ") :]
    print(f"{Colors.GREEN}INFO{Colors.END}: {Colors.GREEN}<-  {Colors.END}", end="")
    _print_query(url, max_file_size, pattern_type, pattern, access_token)
    print(f" | {Colors.PURPLE}{estimated_tokens}{Colors.END}")
