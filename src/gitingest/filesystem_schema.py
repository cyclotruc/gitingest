""" Define the schema for the filesystem representation. """

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from gitingest.utils.ingestion_utils import _get_encoding_list
from gitingest.utils.notebook_utils import process_notebook
from gitingest.utils.textfile_checker_utils import is_textfile

SEPARATOR = "=" * 48


class FileSystemNodeType(Enum):
    """Enum representing the type of a file system node (directory or file)."""

    DIRECTORY = auto()
    FILE = auto()


@dataclass
class FileSystemStats:
    """Class for tracking statistics during file system traversal."""

    visited: set[Path] = field(default_factory=set)
    total_files: int = 0
    total_size: int = 0


@dataclass
class FileSystemNode:  # pylint: disable=too-many-instance-attributes
    """
    Class representing a node in the file system (either a file or directory).

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

    def sort_children(self) -> None:
        """
        Sort the children nodes of a directory according to a specific order.

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
            raise ValueError("Cannot sort children of a non-directory node")

        def _sort_key(child: FileSystemNode) -> tuple[int, str]:
            # Groups: 0=README, 1=regular file, 2=hidden file, 3=regular dir, 4=hidden dir
            name = child.name.lower()
            if child.type == FileSystemNodeType.FILE:
                if name == "readme.md":
                    return (0, name)
                return (1 if not name.startswith(".") else 2, name)
            return (3 if not name.startswith(".") else 4, name)

        self.children.sort(key=_sort_key)

    @property
    def content_string(self) -> str:
        """
        Return the content of the node as a string, including path and content.

        Returns
        -------
        str
            A string representation of the node's content.
        """
        parts = [
            SEPARATOR,
            f"File: {str(self.path_str).replace(os.sep, '/')}",
            SEPARATOR,
            f"{self.content}",
        ]

        return "\n".join(parts) + "\n\n"

    @property
    def content(self) -> str:  # pylint: disable=too-many-return-statements
        """
        Read the content of a file if it's text (or a notebook). Return an error message otherwise.

        Returns
        -------
        str
            The content of the file, or an error message if the file could not be read.

        Raises
        ------
        ValueError
            If the node is a directory.
        """
        if self.type == FileSystemNodeType.DIRECTORY:
            raise ValueError("Cannot read content of a directory node")

        if not is_textfile(self.path):
            return "[Non-text file]"

        if self.path.suffix == ".ipynb":
            try:
                return process_notebook(self.path)
            except Exception as exc:
                return f"Error processing notebook: {exc}"

        # Try multiple encodings
        for encoding in _get_encoding_list():
            try:
                with self.path.open(encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                return f"Error reading file: {exc}"

        return "Error: Unable to decode file with available encodings"
