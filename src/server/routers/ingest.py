"""Ingest endpoint for the API."""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from server.form_types import IntForm, OptStrForm, StrForm
from server.models import IngestErrorResponse, IngestRequest, IngestSuccessResponse, PatternType
from server.query_processor import process_query
from server.server_utils import limiter

router = APIRouter()


@router.post(
    "/api/ingest",
    responses={
        status.HTTP_200_OK: {"model": IngestSuccessResponse, "description": "Successful ingestion"},
        status.HTTP_400_BAD_REQUEST: {"model": IngestErrorResponse, "description": "Bad request or processing error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": IngestErrorResponse, "description": "Internal server error"},
    },
)
@limiter.limit("10/minute")
async def api_ingest(
    request: Request,  # noqa: ARG001 (unused) pylint: disable=unused-argument
    input_text: StrForm,
    max_file_size: IntForm,
    pattern_type: StrForm = "exclude",
    pattern: StrForm = "",
    token: OptStrForm = None,
) -> JSONResponse:
    """Ingest a Git repository and return processed content.

    This endpoint processes a Git repository by cloning it, analyzing its structure,
    and returning a summary with the repository's content. The response includes
    file tree structure, processed content, and metadata about the ingestion.

    Parameters
    ----------
    request : Request
        FastAPI request object
    input_text : StrForm
        Git repository URL or slug to ingest
    max_file_size : IntForm
        Maximum file size slider position (0-500) for filtering files
    pattern_type : StrForm
        Type of pattern to use for file filtering ("include" or "exclude")
    pattern : StrForm
        Glob/regex pattern string for file filtering
    token : OptStrForm
        GitHub personal access token (PAT) for accessing private repositories

    Returns
    -------
    JSONResponse
        Success response with ingestion results or error response with appropriate HTTP status code

    """
    try:
        # Validate input using Pydantic model
        ingest_request = IngestRequest(
            input_text=input_text,
            max_file_size=max_file_size,
            pattern_type=PatternType(pattern_type),
            pattern=pattern,
            token=token,
        )

        result = await process_query(
            input_text=ingest_request.input_text,
            slider_position=ingest_request.max_file_size,
            pattern_type=ingest_request.pattern_type,
            pattern=ingest_request.pattern,
            token=ingest_request.token,
        )

        if isinstance(result, IngestErrorResponse):
            # Return structured error response with 400 status code
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result.model_dump(),
            )

        # Return structured success response with 200 status code
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except ValueError as ve:
        # Handle validation errors with 400 status code
        error_response = IngestErrorResponse(
            error=f"Validation error: {ve!s}",
            repo_url=input_text,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as exc:
        # Handle unexpected errors with 500 status code
        error_response = IngestErrorResponse(
            error=f"Internal server error: {exc!s}",
            repo_url=input_text,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
