"""Expose the file-chunking API for external consumers."""

from .chunker import chunk_file, Chunk

__all__ = ["chunk_file", "Chunk"]
