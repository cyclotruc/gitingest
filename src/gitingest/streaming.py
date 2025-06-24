"""Fetch repository contents directly via the GitHub REST API."""

import base64
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from gitingest.security.path_safety import is_safe_path


def _parse_owner_repo(url: str) -> tuple[str, str]:
    """Extract owner and repository name from a GitHub URL."""
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")
    return parts[0], parts[1]


def stream_remote_repo(
    url: str, branch: Optional[str] = None, subpath: Optional[str] = None, dest: Path = Path(".")
) -> None:
    """Download repository files using the GitHub REST API.

    Parameters
    ----------
    url : str
        Repository URL, e.g. ``https://github.com/user/repo``.
    branch : str, optional
        Branch or commit to download. Defaults to the repo default branch.
    subpath : str, optional
        If provided, only files under this path are downloaded.
    dest : Path
        Destination directory where files will be written.
    """
    owner, repo = _parse_owner_repo(url)
    api_base = f"https://api.github.com/repos/{owner}/{repo}"
    session = requests.Session()
    session.headers.update({"Accept": "application/vnd.github.v3+json"})

    if branch is None:
        repo_info = session.get(api_base, timeout=10)
        repo_info.raise_for_status()
        branch = repo_info.json().get("default_branch", "main")

    tree_resp = session.get(f"{api_base}/git/trees/{branch}?recursive=1", timeout=10)
    tree_resp.raise_for_status()
    tree_data = tree_resp.json()
    for item in tree_data.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item.get("path")
        if subpath:
            normalized = Path(path).as_posix()
            if not normalized.startswith(str(Path(subpath).as_posix()).strip("/")):
                continue
        content_url = f"{api_base}/contents/{path}?ref={branch}"
        file_resp = session.get(content_url, timeout=10)
        file_resp.raise_for_status()
        file_data = file_resp.json()
        if isinstance(file_data, list):
            continue
        content = file_data.get("content", "")
        if file_data.get("encoding") == "base64":
            data = base64.b64decode(content)
        else:
            data = content.encode()
        local_path = dest / path
        if not is_safe_path(dest, local_path):
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data)
