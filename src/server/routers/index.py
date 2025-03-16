"""This module defines the FastAPI router for the home page of the application."""

from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from server.query_processor import process_query
from server.server_config import EXAMPLE_REPOS, templates
from server.server_utils import limiter

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """
    Render the home page with example repositories and default parameters.

    This endpoint serves the home page of the application, rendering the `index.jinja` template
    and providing it with a list of example repositories and default file size values.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.

    Returns
    -------
    HTMLResponse
        An HTML response containing the rendered home page template, with example repositories
        and other default parameters such as file size.
    """
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "examples": EXAMPLE_REPOS,
            "default_file_size": 243,
            "default_file_size_manual": 50,
            "use_manual_input": "false",
            "size_unit": "kb",
        },
    )


@router.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index_post(
    request: Request,
    input_text: str = Form(...),
    max_file_size: int = Form(...),
    max_file_size_manual: Optional[str] = Form(None),
    use_manual_input: bool = Form(...),
    size_unit: str = Form("kb"),
    pattern_type: str = Form(...),
    pattern: str = Form(...),
) -> HTMLResponse:
    """
    Process the form submission with user input for query parameters.

    This endpoint handles POST requests from the home page form. It processes the user-submitted
    input (e.g., text, file size, pattern type) and invokes the `process_query` function to handle
    the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    input_text : str
        The input text provided by the user for processing, by default taken from the form.
    max_file_size : int
        The maximum allowed file size for the input, specified by the user.
    max_file_size_manual : Optional[str], optional
        The manually entered file size, by default None.
    use_manual_input : bool
        Whether to use the manual input instead of the slider, by default False.
    size_unit : str
        The unit for the manual file size input ('kb' or 'mb'), by default 'kb'.
    pattern_type : str
        The type of pattern used for the query, specified by the user.
    pattern : str
        The pattern string used in the query, specified by the user.

    Returns
    -------
    HTMLResponse
        An HTML response containing the results of processing the form input and query logic,
        which will be rendered and returned to the user.
    """
    # Determine the file size based on the input method
    if use_manual_input and max_file_size_manual:
        # Convert the manual input to bytes based on the size unit
        size_value = int(max_file_size_manual)
        if size_unit.lower() == "mb":
            max_file_size = size_value * 1024 * 1024  # Convert MB to bytes
        else:  # Default to KB
            max_file_size = size_value * 1024  # Convert KB to bytes

    return await process_query(
        request,
        input_text,
        max_file_size,
        pattern_type,
        pattern,
        is_index=True,
        is_file_size_manual=use_manual_input,
        size_unit=size_unit,
    )
