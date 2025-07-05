"""Process a query by parsing input, cloning a repository, and generating a summary."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from gitingest.clone import clone_repo
from gitingest.ingestion import ingest_query
from gitingest.query_parser import IngestionQuery, parse_query
from gitingest.utils.git_utils import validate_github_token
from server.models import IngestErrorResponse, IngestResponse, IngestSuccessResponse
from server.server_config import MAX_DISPLAY_SIZE
from server.server_utils import Colors, log_slider_to_size


async def process_query(
    input_text: str,
    slider_position: int,
    pattern_type: str = "exclude",
    pattern: str = "",
    token: str | None = None,
) -> IngestResponse:
    """Process a query by parsing input, cloning a repository, and generating a summary.

    Handle user input, process Git repository data, and prepare
    a response for rendering a template with the processed results or an error message.

    Parameters
    ----------
    input_text : str
        Input text provided by the user, typically a Git repository URL or slug.
    slider_position : int
        Position of the slider, representing the maximum file size in the query.
    pattern_type : str
        Type of pattern to use (either "include" or "exclude") (default: ``"exclude"``).
    pattern : str
        Pattern to include or exclude in the query, depending on the pattern type.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    Returns
    -------
    IngestResponse
        A union type, corresponding to IngestErrorResponse or IngestSuccessResponse

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
        msg = f"Invalid pattern type: {pattern_type}"
        raise ValueError(msg)

    if token:
        validate_github_token(token)

    max_file_size = log_slider_to_size(slider_position)

    query: IngestionQuery | None = None
    short_repo_url = ""

    try:
        query = await parse_query(
            source=input_text,
            max_file_size=max_file_size,
            from_web=True,
            include_patterns=include_patterns,
            ignore_patterns=exclude_patterns,
            token=token,
        )
        query.ensure_url()

        # Sets the "<user>/<repo>" for the page title
        short_repo_url = f"{query.user_name}/{query.repo_name}"

        clone_config = query.extract_clone_config()
        await clone_repo(clone_config, token=token)

        summary, tree, content = ingest_query(query)

        local_txt_file = Path(clone_config.local_path).with_suffix(".txt")

        with local_txt_file.open("w", encoding="utf-8") as f:
            f.write(tree + "\n" + content)

    except Exception as exc:
        if query and query.url:
            _print_error(query.url, exc, max_file_size, pattern_type, pattern)
        else:
            print(f"{Colors.BROWN}WARN{Colors.END}: {Colors.RED}<-  {Colors.END}", end="")
            print(f"{Colors.RED}{exc}{Colors.END}")

        return IngestErrorResponse(error=str(exc))

    if len(content) > MAX_DISPLAY_SIZE:
        content = (
            f"(Files content cropped to {int(MAX_DISPLAY_SIZE / 1_000)}k characters, "
            "download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        )

    query.ensure_url()
    query.url = cast("str", query.url)

    _print_success(
        url=query.url,
        max_file_size=max_file_size,
        pattern_type=pattern_type,
        pattern=pattern,
        summary=summary,
    )

    return IngestSuccessResponse(
        repo_url=input_text,
        short_repo_url=short_repo_url,
        summary=summary,
        ingest_id=query.id,
        tree=tree,
        content=content,
        default_max_file_size=slider_position,
        pattern_type=pattern_type,
        pattern=pattern,
    )


def _print_query(url: str, max_file_size: int, pattern_type: str, pattern: str) -> None:
    """Print a formatted summary of the query details for debugging.

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
    default_max_file_kb = 50
    print(f"{Colors.WHITE}{url:<20}{Colors.END}", end="")
    if int(max_file_size / 1024) != default_max_file_kb:
        print(
            f" | {Colors.YELLOW}Size: {int(max_file_size / 1024)}kB{Colors.END}",
            end="",
        )
    if pattern_type == "include" and pattern != "":
        print(f" | {Colors.YELLOW}Include {pattern}{Colors.END}", end="")
    elif pattern_type == "exclude" and pattern != "":
        print(f" | {Colors.YELLOW}Exclude {pattern}{Colors.END}", end="")


def _print_error(url: str, exc: Exception, max_file_size: int, pattern_type: str, pattern: str) -> None:
    """Print a formatted error message for debugging.

    Parameters
    ----------
    url : str
        The URL associated with the query that caused the error.
    exc : Exception
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
    print(f" | {Colors.RED}{exc}{Colors.END}")


def _print_success(url: str, max_file_size: int, pattern_type: str, pattern: str, summary: str) -> None:
    """Print a formatted success message for debugging.

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
