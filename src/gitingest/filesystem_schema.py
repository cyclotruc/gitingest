""" Define the schema for the filesystem representation. """

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from gitingest.exceptions import InvalidNotebookError
from gitingest.utils.ingestion_utils import _get_encoding_list
from gitingest.utils.notebook_utils import process_notebook
from gitingest.utils.textfile_checker_utils import is_textfile

SEPARATOR = "=" * 48 + "\n"


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

    This class has more than the recommended number of attributes because it needs to
    track various properties of files and directories for comprehensive analysis.
    """

    name: str
    type: FileSystemNodeType  # e.g., "directory" or "file"
    path_str: str
    path: Path
    size: int = 0
    file_count: int = 0
    dir_count: int = 0
    depth: int = 0
    children: list[FileSystemNode] = field(default_factory=list)  # Using default_factory instead of empty list

    def sort_children(self) -> None:
        """
        Sort the children nodes of a directory according to a specific order.

        Order of sorting:
        1. README.md first
        2. Regular files (not starting with dot)
        3. Hidden files (starting with dot)
        4. Regular directories (not starting with dot)
        5. Hidden directories (starting with dot)
        All groups are sorted alphanumerically within themselves.
        """
        # Separate files and directories
        files = [child for child in self.children if child.type == FileSystemNodeType.FILE]
        directories = [child for child in self.children if child.type == FileSystemNodeType.DIRECTORY]

        # Find README.md
        readme_files = [f for f in files if f.name.lower() == "readme.md"]
        other_files = [f for f in files if f.name.lower() != "readme.md"]

        # Separate hidden and regular files/directories
        regular_files = [f for f in other_files if not f.name.startswith(".")]
        hidden_files = [f for f in other_files if f.name.startswith(".")]
        regular_dirs = [d for d in directories if not d.name.startswith(".")]
        hidden_dirs = [d for d in directories if d.name.startswith(".")]

        # Sort each group alphanumerically
        regular_files.sort(key=lambda x: x.name)
        hidden_files.sort(key=lambda x: x.name)
        regular_dirs.sort(key=lambda x: x.name)
        hidden_dirs.sort(key=lambda x: x.name)

        self.children = readme_files + regular_files + hidden_files + regular_dirs + hidden_dirs

    @property
    def content_string(self) -> str:
        """
        Return the content of the node as a string.

        This property returns the content of the node as a string, including the path and content.

        Returns
        -------
        str
            A string representation of the node's content.
        """
        content_repr = SEPARATOR

        # Use forward slashes in output paths
        content_repr += f"File: {str(self.path_str).replace(os.sep, '/')}\n"
        content_repr += SEPARATOR
        content_repr += f"{self.content}\n\n"
        return content_repr

    @property
    def content(self) -> str:  # pylint: disable=too-many-return-statements
        """
        Read the content of a file.

        This function attempts to open a file and read its contents using UTF-8 encoding.
        If an error occurs during reading (e.g., file is not found or permission error),
        it returns an error message.

        Returns
        -------
        str
            The content of the file, or an error message if the file could not be read.
        """
        if self.type == FileSystemNodeType.FILE and not is_textfile(self.path):
            return "[Non-text file]"

        try:
            if self.path.suffix == ".ipynb":
                try:
                    return process_notebook(self.path)
                except Exception as exc:
                    return f"Error processing notebook: {exc}"

            for encoding in _get_encoding_list():
                try:
                    with self.path.open(encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
                except OSError as exc:
                    return f"Error reading file: {exc}"

            return "Error: Unable to decode file with available encodings"

        except (OSError, InvalidNotebookError) as exc:
            return f"Error reading file: {exc}"
