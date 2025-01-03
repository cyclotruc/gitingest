from urllib.parse import unquote_plus

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from process_query import process_query
from server_utils import limiter

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/{full_path:path}")
async def catch_all(
    request: Request,
    full_path: str,
    include: str | None = Query(default=None),
    exclude: str | None = Query(default=None),
    pattern: str | None = Query(default=None),
    pattern_type: str | None = Query(default="exclude"),
) -> HTMLResponse:
    """
    Renders a page with a GitHub URL based on the provided path.

    This endpoint catches all GET requests with a dynamic path, constructs a GitHub URL
    using the `full_path` parameter, and renders the `github.jinja` template with that URL.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    full_path : str
        The full path extracted from the URL, which is used to build the GitHub URL.
    include : str | None
        Include pattern for files, if provided.
    exclude : str | None
        Exclude pattern for files, if provided.
    pattern : str | None
        Generic pattern to use with pattern_type.
    pattern_type : str | None
        Type of pattern (include/exclude) to use with pattern.

    Returns
    -------
    HTMLResponse
        An HTML response containing the rendered template.
    """
    # Handle both pattern_type+pattern and direct include/exclude parameters
    actual_pattern = ""
    actual_pattern_type = pattern_type

    if include:
        actual_pattern = unquote_plus(include)
        actual_pattern_type = "include"
    elif exclude:
        actual_pattern = unquote_plus(exclude)
        actual_pattern_type = "exclude"
    elif pattern:
        actual_pattern = unquote_plus(pattern)

    return templates.TemplateResponse(
        "github.jinja",
        {
            "request": request,
            "github_url": f"https://github.com/{full_path}",
            "loading": True,
            "default_file_size": 243,
            "pattern_type": actual_pattern_type,
            "pattern": actual_pattern,
        },
    )


@router.post("/{full_path:path}", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def process_catch_all(
    request: Request,
    repo: str = Form(...),
    include_files_under: int = Form(...),
    pattern_type: str = Form(...),
    pattern: str = Form(...),
) -> HTMLResponse:
    """
    Processes the form submission with user input for query parameters.

    This endpoint handles POST requests, processes the input parameters (e.g., text, file size, pattern),
    and calls the `process_query` function to handle the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    repo : str
        The repository URL or local path provided by the user.
    include_files_under : int
        The maximum allowed file size for the input, specified by the user.
    pattern_type : str
        The type of pattern used for the query, specified by the user.
    pattern : str
        The pattern string used in the query, specified by the user.

    Returns
    -------
    HTMLResponse
        An HTML response generated after processing the form input and query logic.
    """
    return await process_query(
        request,
        repo,
        include_files_under,
        pattern_type,
        pattern,
        is_index=False,
    )
