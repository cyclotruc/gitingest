""" Gitingest: A package for ingesting data from Git repositories. """

from core.query_ingestion import run_ingest_query
from core.query_parser import parse_query
from core.repository_clone import clone_repo
from core.repository_ingest import ingest

__all__ = ["run_ingest_query", "clone_repo", "parse_query", "ingest"]
