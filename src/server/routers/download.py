"""Module containing the FastAPI router for downloading a digest file."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from gitingest.config import TMP_BASE_PATH

router = APIRouter()


@router.get("/download/{digest_id}", response_class=FileResponse)
async def download_ingest(digest_id: str) -> FileResponse:
    """Return the first ``*.txt`` file produced for ``digest_id`` as a download.

    Parameters
    ----------
    digest_id : str
        Identifier that the ingest step emitted (also the directory name that stores the artefacts).

    Returns
    -------
    FileResponse
        Streamed response with media type ``text/plain`` that prompts the browser to download the file.

    Raises
    ------
    HTTPException
        **404** - digest directory is missing or contains no ``*.txt`` file.
        **403** - the process lacks permission to read the directory or file.

    """
    directory = TMP_BASE_PATH / digest_id

    if not directory.is_dir():
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Digest {digest_id!r} not found")

    try:
        first_txt_file = next(directory.glob("*.txt"))
    except StopIteration as exc:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No .txt file found for digest {digest_id!r}",
        ) from exc

    try:
        return FileResponse(path=first_txt_file, media_type="text/plain", filename=first_txt_file.name)
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"Permission denied for {first_txt_file}") from exc
