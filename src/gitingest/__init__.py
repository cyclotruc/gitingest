""" Gitingest: A package for ingesting data from git repositories. """

from gitingest.query_ingestion import run_ingest_query
from gitingest.query_parser import parse_query
from gitingest.repository_clone import clone_repo
from gitingest.repository_ingest import ingest

__all__ = ["run_ingest_query", "clone_repo", "parse_query", "ingest"]
