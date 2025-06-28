"""The dynamic router module defines handlers for dynamic path requests."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from gitingest.utils.compat_typing import Annotated
from server.models import QueryForm
from server.query_processor import process_query
from server.server_config import templates
from server.server_utils import limiter

router = APIRouter()


@router.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str) -> HTMLResponse:
    """Render a page with a Git URL based on the provided path.

    This endpoint catches all GET requests with a dynamic path, constructs a Git URL
    using the ``full_path`` parameter, and renders the ``git.jinja`` template with that URL.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    full_path : str
        The full path extracted from the URL, which is used to build the Git URL.

    Returns
    -------
    HTMLResponse
        An HTML response containing the rendered template, with the Git URL
        and other default parameters such as loading state and file size.

    """
    return templates.TemplateResponse(
        "git.jinja",
        {
            "request": request,
            "repo_url": full_path,
            "loading": True,
            "default_file_size": 243,
        },
    )


@router.post("/{full_path:path}", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def process_catch_all(request: Request, form: Annotated[QueryForm, Depends(QueryForm.as_form)]) -> HTMLResponse:
    """Process the form submission with user input for query parameters.

    This endpoint handles POST requests, processes the input parameters (e.g., text, file size, pattern),
    and calls the ``process_query`` function to handle the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        FastAPI request context.
    form : Annotated[QueryForm, Depends(QueryForm.as_form)]
        The form data submitted by the user.

    Returns
    -------
    HTMLResponse
        Rendered HTML with the query results.

    """
    resolved_token = form.token if form.token else None
    return await process_query(
        request,
        input_text=form.input_text,
        slider_position=form.max_file_size,
        pattern_type=form.pattern_type,
        pattern=form.pattern,
        is_index=False,
        token=resolved_token,
    )
