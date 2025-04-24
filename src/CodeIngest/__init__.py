"""Gitingest: A package for ingesting data from Git repositories."""

from CodeIngest.cloning import clone_repo
from CodeIngest.entrypoint import ingest, ingest_async
from CodeIngest.ingestion import ingest_query
from CodeIngest.query_parsing import parse_query

__all__ = ["ingest_query", "clone_repo", "parse_query", "ingest", "ingest_async"]
