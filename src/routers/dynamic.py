import typing

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from process_query import process_query
from server_utils import limiter

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/extract/{full_path:path}", response_model=None)
async def extract_content(
    request: Request,
    full_path: str,
    summary: bool = False,
) -> Response:
    try:
        query_params = request.query_params
        max_file_size = int(query_params.get("max_file_size", 243))
        pattern_type = query_params.get("pattern_type", "exclude")
        pattern = query_params.get("pattern", "")

        processed_query = await process_query(
            request,
            input_text=f"https://github.com/{full_path}",
            slider_position=max_file_size,
            pattern_type=pattern_type,
            pattern=pattern,
            is_index=False,
            raw_response=True,
        )

        result_summary, tree, content = typing.cast(tuple[str, str, str], processed_query)

        response_parts = []
        if summary:
            response_parts.append(f"Summary:\n{result_summary}\n")
            response_parts.append(f"Tree:\n{tree}\n")
        response_parts.append(f"Content:\n{content}")

        return Response(content="\n".join(response_parts), media_type="text/plain")
    except Exception as e:
        return Response(
            content=f"Error during extraction: {str(e)}",
            media_type="text/plain",
            status_code=500,
        )


@router.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str) -> HTMLResponse:
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

    Returns
    -------
    HTMLResponse
        An HTML response containing the rendered template, with the GitHub URL
        and other default parameters such as loading state and file size.
    """
    return templates.TemplateResponse(
        "github.jinja",
        {
            "request": request,
            "github_url": f"https://github.com/{full_path}",
            "loading": True,
            "default_file_size": 243,
        },
    )


@router.post("/{full_path:path}", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def process_catch_all(
    request: Request,
    input_text: str = Form(...),
    max_file_size: int = Form(...),
    pattern_type: str = Form(...),
    pattern: str = Form(...),
) -> HTMLResponse | tuple[str, str, str]:
    """
    Processes the form submission with user input for query parameters.

    This endpoint handles POST requests, processes the input parameters (e.g., text, file size, pattern),
    and calls the `process_query` function to handle the query logic, returning the result as an HTML response.

    Parameters
    ----------
    request : Request
        The incoming request object, which provides context for rendering the response.
    input_text : str, optional
        The input text provided by the user for processing, by default taken from the form.
    max_file_size : int, optional
        The maximum allowed file size for the input, specified by the user.
    pattern_type : str, optional
        The type of pattern used for the query, specified by the user.
    pattern : str, optional
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
