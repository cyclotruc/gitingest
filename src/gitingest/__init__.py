"""Gitingest: A package for ingesting data from Git repositories."""

from gitingest.clone import clone_repo
from gitingest.entrypoint import ingest, ingest_async
from gitingest.ingestion import ingest_query
from gitingest.query_parser import parse_query

__all__ = ["clone_repo", "ingest", "ingest_async", "ingest_query", "parse_query"]
