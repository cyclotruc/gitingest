from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import EXAMPLE_REPOS
from process_query import process_query
from server_utils import limiter

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    repo: str | None = Query(default=None),
    pattern_type: str | None = Query(default="exclude"),
    pattern: str | None = Query(default=""),
    include_files_under: int | None = Query(default=243),
) -> HTMLResponse:
    """
    Renders the home page with example repositories and default parameters.
    Now supports query parameters for deep linking.
    """
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "examples": EXAMPLE_REPOS,
            "default_file_size": include_files_under,
            "github_url": repo if repo else "",
            "pattern_type": pattern_type,
            "pattern": pattern,
        },
    )


@router.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index_post(
    request: Request,
    repo: str = Form(...),
    include_files_under: int = Form(...),
    pattern_type: str = Form(...),
    pattern: str = Form(...),
) -> HTMLResponse:
    """
    Processes the form submission with user input for query parameters.

    This endpoint handles POST requests from the home page form. It processes the user-submitted
    input (e.g., text, file size, pattern type) and invokes the `process_query` function to handle
    the query logic, returning the result as an HTML response.

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
        An HTML response containing the results of processing the form input and query logic.
    """
    return await process_query(
        request,
        repo,
        include_files_under,
        pattern_type,
        pattern,
        is_index=True,
    )
