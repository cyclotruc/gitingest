"""Prometheus metrics endpoint for the API."""

import os
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from prometheus_client import REGISTRY, generate_latest

router = APIRouter()

@router.get("/metrics")
async def metrics(request: Request) -> HTMLResponse:
    """Serve Prometheus metrics with token authentication.
    
    This endpoint requires the GITINGEST_PROMETHEUS_TOKEN to be provided
    in the Authorization header as 'Bearer <token>'.
    
    Parameters
    ----------
    request : Request
        The incoming HTTP request containing headers
        
    Returns
    -------
    HTMLResponse
        Prometheus metrics in text format
        
    Raises
    ------
    HTTPException
        401 if no token provided or invalid token
    """
    # Get the expected token from environment
    expected_token = os.getenv("GITINGEST_PROMETHEUS_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Extract and verify token
    provided_token = auth_header[7:]  # Remove "Bearer " prefix
    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return HTMLResponse(content=generate_latest(REGISTRY), status_code=200, media_type="text/plain")
