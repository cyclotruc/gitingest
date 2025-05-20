"""This module defines the dynamic router for handling dynamic path requests."""

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from server.query_processor import process_query
from server.server_config import templates
from server.server_utils import limiter

router = APIRouter()


@router.get("/github.com/{user}/{repo}")
async def redirect_github_path(user: str, repo: str):
    """
    Redirect /github.com/username/repo to /username/repo for convenience.
    """
    return RedirectResponse(url=f"/{user}/{repo}", status_code=307)


@router.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str) -> HTMLResponse:
    """
    Render docs for a GitHub repo based on the provided path, auto-processing if the path matches username/repo.
    """
    # If the path looks like username/repo or username/repo/..., treat it as a GitHub repo
    path_parts = full_path.strip("/").split("/")
    repo_url = full_path
    loading = True
    error_message = None
    if len(path_parts) >= 2 and path_parts[0] and path_parts[1]:
        # Only allow valid GitHub repo slugs (no .git, no extra slashes)
        user, repo = path_parts[0], path_parts[1]
        # Optionally support subpaths (e.g., username/repo/tree/main/path)
        subpath = "/".join(path_parts[2:]) if len(path_parts) > 2 else ""
        github_url = f"https://github.com/{user}/{repo}"
        if subpath:
            github_url += f"/{subpath}"
        repo_url = github_url
        # Auto-process the repo and render docs
        try:
            return await process_query(
                request,
                repo_url,
                243,  # default file size
                pattern_type="exclude",
                pattern="",
                is_index=False,
            )
        except Exception as exc:
            error_message = str(exc)
            loading = False
    # If not a valid repo path, just show the form with error (or fallback)
    return templates.TemplateResponse(
        "git.jinja",
        {
            "request": request,
            "repo_url": repo_url,
            "loading": loading,
            "default_file_size": 243,
            "error_message": error_message,
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
) -> HTMLResponse:
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
