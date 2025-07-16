"""Define the schema for the filesystem representation.

Memory optimization:
- Lazy loading: File content is only loaded when the content property is accessed
- Content caching: Content is cached to avoid repeated file reads
- Cache clearing: The clear_content_cache method allows freeing memory when content is no longer needed
- Chunked reading: Large files are read in chunks to avoid loading everything at once
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from gitingest.utils.compat_func import readlink
from gitingest.utils.file_utils import _decodes, _get_preferred_encodings, _read_chunk
from gitingest.utils.notebook import process_notebook

if TYPE_CHECKING:
    from pathlib import Path

SEPARATOR = "=" * 48  # Tiktoken, the tokenizer openai uses, counts 2 tokens if we have more than 48


class FileSystemNodeType(Enum):
    """Enum representing the type of a file system node (directory or file)."""

    DIRECTORY = auto()
    FILE = auto()
    SYMLINK = auto()


@dataclass
class FileSystemStats:
    """Class for tracking statistics during file system traversal."""

    total_files: int = 0
    total_size: int = 0


@dataclass
class FileSystemNode:  # pylint: disable=too-many-instance-attributes
    """Class representing a node in the file system (either a file or directory).

    Tracks properties of files/directories for comprehensive analysis.
    """

    name: str
    type: FileSystemNodeType
    path_str: str
    path: Path
    size: int = 0
    file_count: int = 0
    dir_count: int = 0
    depth: int = 0
    children: list[FileSystemNode] = field(default_factory=list)
    _content_cache: str | None = field(default=None, repr=False)

    def sort_children(self) -> None:
        """Sort the children nodes of a directory according to a specific order.

        Order of sorting:
          2. Regular files (not starting with dot)
          3. Hidden files (starting with dot)
          4. Regular directories (not starting with dot)
          5. Hidden directories (starting with dot)

        All groups are sorted alphanumerically within themselves.

        Raises
        ------
        ValueError
            If the node is not a directory.

        """
        if self.type != FileSystemNodeType.DIRECTORY:
            msg = "Cannot sort children of a non-directory node"
            raise ValueError(msg)

        def _sort_key(child: FileSystemNode) -> tuple[int, str]:
            # returns the priority order for the sort function, 0 is first
            # Groups: 0=README, 1=regular file, 2=hidden file, 3=regular dir, 4=hidden dir
            name = child.name.lower()
            if child.type == FileSystemNodeType.FILE:
                if name == "readme" or name.startswith("readme."):
                    return (0, name)
                return (1 if not name.startswith(".") else 2, name)
            return (3 if not name.startswith(".") else 4, name)

        self.children.sort(key=_sort_key)

    def clear_content_cache(self) -> None:
        """Clear the cached content to free up memory.

        This method clears the content cache of this node and all its children recursively,
        allowing the garbage collector to reclaim memory used by file contents.
        """
        self._content_cache = None

        # Recursively clear cache for all children
        for child in self.children:
            child.clear_content_cache()

    @property
    def content_string(self) -> str:
        """Return the content of the node as a string, including path and content.

        Returns
        -------
        str
            A string representation of the node's content.

        """
        parts = [
            SEPARATOR,
            f"{self.type.name}: {str(self.path_str).replace(os.sep, '/')}"
            + (f" -> {readlink(self.path).name}" if self.type == FileSystemNodeType.SYMLINK else ""),
            SEPARATOR,
            f"{self.content}",
        ]

        return "\n".join(parts) + "\n\n"

    @property
    def content(self) -> str:  # pylint: disable=too-many-return-statements,too-many-branches  # noqa: C901, PLR0912
        """Return file content (if text / notebook) or an explanatory placeholder.

        Heuristically decides whether the file is text or binary by decoding a small chunk of the file
        with multiple encodings and checking for common binary markers.

        Uses lazy loading to avoid loading the entire file into memory until needed,
        and caches the result to avoid repeated file reads.

        Returns
        -------
        str
            The content of the file, or an error message if the file could not be read.

        Raises
        ------
        ValueError
            If the node is a directory.

        """
        # Return cached content if available
        if self._content_cache is not None:
            return self._content_cache

        if self.type == FileSystemNodeType.DIRECTORY:
            msg = "Cannot read content of a directory node"
            raise ValueError(msg)

        if self.type == FileSystemNodeType.SYMLINK:
            self._content_cache = ""  # TODO: are we including the empty content of symlinks?
            return self._content_cache

        if self.path.suffix == ".ipynb":  # Notebook
            try:
                self._content_cache = process_notebook(self.path)
            except Exception as exc:
                self._content_cache = f"Error processing notebook: {exc}"
            return self._content_cache

        chunk = _read_chunk(self.path)

        if chunk is None:
            self._content_cache = "Error reading file"
            return self._content_cache

        if chunk == b"":
            self._content_cache = "[Empty file]"
            return self._content_cache

        if not _decodes(chunk, "utf-8"):
            self._content_cache = "[Binary file]"
            return self._content_cache

        # Find the first encoding that decodes the sample
        good_enc: str | None = next(
            (enc for enc in _get_preferred_encodings() if _decodes(chunk, encoding=enc)),
            None,
        )

        if good_enc is None:
            self._content_cache = "Error: Unable to decode file with available encodings"
            return self._content_cache

        try:
            # Read file in chunks to avoid loading large files entirely into memory
            # For very large files, we'll read and process in smaller chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            file_size = self.path.stat().st_size

            # For files larger than 10MB, use a more memory-efficient approach
            if file_size > 10 * 1024 * 1024:
                # Read just enough to give a meaningful preview
                preview_size = 1024 * 100  # 100KB preview
                with self.path.open(encoding=good_enc) as fp:
                    preview = fp.read(preview_size)

                self._content_cache = (
                    f"{preview}\n\n[... File truncated (total size: {file_size / (1024 * 1024):.1f} MB) ...]"
                )
            else:
                # For smaller files, read in chunks but still load into memory
                content_chunks = []
                with self.path.open(encoding=good_enc) as fp:
                    while True:
                        chunk = fp.read(chunk_size)
                        if not chunk:
                            break
                        content_chunks.append(chunk)

                self._content_cache = "".join(content_chunks)
        except (OSError, UnicodeDecodeError) as exc:
            self._content_cache = f"Error reading file with {good_enc!r}: {exc}"

        return self._content_cache
