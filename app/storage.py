import os
import uuid
from pathlib import Path

from fastapi import UploadFile


UPLOADS_DIR = Path("uploads")


def ensure_uploads_dir() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(original: str) -> str:
    name = os.path.basename(original)
    name = name.replace("\x00", "")
    return name or "file"


async def save_upload(file: UploadFile) -> tuple[str, str, int]:
    ensure_uploads_dir()

    original = safe_filename(file.filename or "file")
    stored = f"{uuid.uuid4().hex}_{original}"
    path = UPLOADS_DIR / stored

    size = 0
    with path.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    return original, stored, size
