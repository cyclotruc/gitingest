""" This module defines the dynamic router for handling dynamic path requests. """

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from typing import Union

from server.query_processor import process_query
from server.server_config import templates
from server.server_utils import is_browser, limiter

router = APIRouter()


@router.get("/{full_path:path}", response_model=None)
async def catch_all(request: Request, full_path: str) -> Union[HTMLResponse, Response]:
    """
    Render a page with a Git URL based on the provided path.

    This endpoint catches all GET requests with a dynamic path, constructs a Git URL
    using the `full_path` parameter, and renders the `git.jinja` template with that URL.
    
    For non-browser requests, it also accepts query parameters:
    - max_size: Maximum file size (slider position 0-500)
    - pattern_type: Type of pattern ("include" or "exclude")
    - pattern: Pattern string to include or exclude
    - format: Response format ("text" or "json")

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    full_path : str
        The full path extracted from the URL, which is used to build the Git URL.

    Returns
    -------
    HTMLResponse or Response
        An HTML response for browsers or a response in the requested format for API clients.
    """

    # Check if the request is from a browser based on User-Agent
    wants_html = is_browser(request)
    
    if not wants_html:
        # Extract query parameters with defaults
        query_params = request.query_params
        max_size = int(query_params.get("max_size", "243"))
        pattern_type = query_params.get("pattern_type", "exclude")
        pattern = query_params.get("pattern", "")
        
        # Determine format based on Accept header or format parameter
        format_param = query_params.get("format", "text")
        accept_header = request.headers.get("Accept", "text/plain")
        
        if "application/json" in accept_header or format_param == "json":
            response_format = "json"
        else:
            response_format = "text"  # Default
        
        return await process_query(
            request,
            full_path,  # Use the path as the input text
            max_size,   # Use provided max_size or default
            pattern_type,  # Use provided pattern_type or default
            pattern,    # Use provided pattern or default
            is_index=False,
            response_format=response_format,  # Format parameter
        )
    else:
        return templates.TemplateResponse(
            "git.jinja",
            {
                "request": request,
                "repo_url": full_path,
                "loading": True,
                "default_file_size": 243,
            },
        )


@router.post("/{full_path:path}", response_model=None)
@limiter.limit("10/minute")
async def process_catch_all(
    request: Request,
    input_text: str = Form(...),
    max_file_size: int = Form(...),
    pattern_type: str = Form(...),
    pattern: str = Form(...),
) -> Union[HTMLResponse, Response]:
    """
    Process the form submission with user input for query parameters.

    This endpoint handles POST requests, processes the input parameters (e.g., text, file size, pattern),
    and calls the `process_query` function to handle the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    input_text : str
        The input text provided by the user for processing, by default taken from the form.
    max_file_size : int
        The maximum allowed file size for the input, specified by the user.
    pattern_type : str
        The type of pattern used for the query, specified by the user.
    pattern : str
        The pattern string used in the query, specified by the user.

    Returns
    -------
    HTMLResponse
        An HTML response generated after processing the form input and query logic,
        which will be rendered and returned to the user.
    """
    return await process_query(
        request,
        input_text,
        max_file_size,
        pattern_type,
        pattern,
        is_index=False,
    )
