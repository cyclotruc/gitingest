""" Gitingest: A package for ingesting data from Git repositories. """

from gitingest.cloning import clone_repo
from gitingest.ingestion import ingest_query
from gitingest.query_parsing import parse_query
from gitingest.repository_ingest import ingest, ingest_async

__all__ = ["ingest_query", "clone_repo", "parse_query", "ingest", "ingest_async"]
