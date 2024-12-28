import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from config import TMP_BASE_PATH

router = APIRouter()


@router.get("/download/{digest_id}")
async def download_ingest(digest_id: str) -> Response:
    try:
        # Find the first .txt file in the directory
        directory = f"{TMP_BASE_PATH}/{digest_id}"
        txt_files = [f for f in os.listdir(directory) if f.endswith(".txt")]

        if not txt_files:
            raise FileNotFoundError("No .txt file found")

        with open(f"{directory}/{txt_files[0]}") as f:
            content = f.read()

        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={txt_files[0]}"},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Digest not found")
