""" This module contains the dataclasses for the ingestion process. """

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

from gitingest.config import MAX_FILE_SIZE


@dataclass
class CloneConfig:
    """
    Configuration for cloning a Git repository.

    This class holds the necessary parameters for cloning a repository to a local path, including
    the repository's URL, the target local path, and optional parameters for a specific commit or branch.

    Attributes
    ----------
    url : str
        The URL of the Git repository to clone.
    local_path : str
        The local directory where the repository will be cloned.
    commit : str, optional
        The specific commit hash to check out after cloning (default is None).
    branch : str, optional
        The branch to clone (default is None).
    subpath : str
        The subpath to clone from the repository (default is "/").
    """

    url: str
    local_path: str
    commit: Optional[str] = None
    branch: Optional[str] = None
    subpath: str = "/"
    blob: bool = False


@dataclass
class IngestionQuery:  # pylint: disable=too-many-instance-attributes
    """
    Dataclass to store the parsed details of the repository or file path.
    """

    user_name: Optional[str]
    repo_name: Optional[str]
    local_path: Path
    url: Optional[str]
    slug: str
    id: str
    subpath: str = "/"
    type: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    max_file_size: int = MAX_FILE_SIZE
    ignore_patterns: Optional[Set[str]] = None
    include_patterns: Optional[Set[str]] = None
    pattern_type: Optional[str] = None

    def extact_clone_config(self) -> CloneConfig:
        """
        Extract the relevant fields for the CloneConfig object.

        Returns
        -------
        CloneConfig
            A CloneConfig object containing the relevant fields.

        Raises
        ------
        ValueError
            If the 'url' parameter is not provided.
        """
        if not self.url:
            raise ValueError("The 'url' parameter is required.")

        return CloneConfig(
            url=self.url,
            local_path=str(self.local_path),
            commit=self.commit,
            branch=self.branch,
            subpath=self.subpath,
            blob=self.type == "blob",
        )
