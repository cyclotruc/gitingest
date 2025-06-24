"""Gitingest: A package for ingesting data from Git repositories."""

from gitingest.cloning import clone_repo
from gitingest.entrypoint import ingest, ingest_async
from gitingest.streaming import stream_remote_repo
from gitingest.ingestion import ingest_query
from gitingest.query_parsing import parse_query

__all__ = [
    "ingest_query",
    "clone_repo",
    "parse_query",
    "ingest",
    "ingest_async",
    "stream_remote_repo",
]
