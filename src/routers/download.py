""" This module contains the FastAPI router for downloading a digest file. """

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from config import TMP_BASE_PATH

router = APIRouter()


@router.get("/download/{digest_id}")
async def download_ingest(digest_id: str) -> Response:
    """
    Downloads a .txt file associated with a given digest ID.

    This function searches for a `.txt` file in a directory corresponding to the provided
    digest ID. If a file is found, it is read and returned as a downloadable attachment.
    If no `.txt` file is found, an error is raised.

    Parameters
    ----------
    digest_id : str
        The unique identifier for the digest. It is used to find the corresponding directory
        and locate the .txt file within that directory.

    Returns
    -------
    Response
        A FastAPI Response object containing the content of the found `.txt` file. The file is
        sent with the appropriate media type (`text/plain`) and the correct `Content-Disposition`
        header to prompt a file download.

    Raises
    ------
    HTTPException
        If the digest directory is not found or if no `.txt` file exists in the directory.
    """
    directory = f"{TMP_BASE_PATH}/{digest_id}"

    try:
        if not os.path.exists(directory):
            raise FileNotFoundError("Directory not found")

        txt_files = [f for f in os.listdir(directory) if f.endswith(".txt")]
        if not txt_files:
            raise FileNotFoundError("No .txt file found")

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Digest not found") from exc

    # Find the first .txt file in the directory
    first_file = txt_files[0]

    with open(f"{directory}/{first_file}", encoding="utf-8") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={first_file}"},
    )
