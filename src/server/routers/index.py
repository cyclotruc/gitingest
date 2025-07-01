"""Module defining the FastAPI router for the home page of the application."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from gitingest.utils.compat_typing import Annotated
from server.models import QueryForm
from server.query_processor import process_query
from server.server_config import EXAMPLE_REPOS, templates
from server.server_utils import limiter

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Render the home page with example repositories and default parameters.

    This endpoint serves the home page of the application, rendering the ``index.jinja`` template
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
        },
    )


@router.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def index_post(request: Request, form: Annotated[QueryForm, Depends(QueryForm.as_form)]) -> HTMLResponse:
    """Process the form submission with user input for query parameters.

    This endpoint handles POST requests from the home page form. It processes the user-submitted
    input (e.g., text, file size, pattern type) and invokes the ``process_query`` function to handle
    the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    form : Annotated[QueryForm, Depends(QueryForm.as_form)]
        The form data submitted by the user.

    Returns
    -------
    HTMLResponse
        An HTML response containing the results of processing the form input and query logic,
        which will be rendered and returned to the user.

    """
    resolved_token = form.token if form.token else None
    return await process_query(
        request,
        input_text=form.input_text,
        slider_position=form.max_file_size,
        pattern_type=form.pattern_type,
        pattern=form.pattern,
        is_index=True,
        token=resolved_token,
    )
