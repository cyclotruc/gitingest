"""Module containing the routers for the FastAPI application."""

from server.routers.dynamic import router as dynamic
from server.routers.index import router as index
from server.routers.ingest import router as ingest
from server.routers.metrics import router as metrics

__all__ = ["dynamic", "index", "ingest", "metrics"]
