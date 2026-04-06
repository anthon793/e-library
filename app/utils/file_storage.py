from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse

from fastapi import UploadFile
import httpx

from app.config import settings


def ensure_storage_dir() -> str:
    path = os.path.join(settings.UPLOAD_DIR, "hybrid")
    os.makedirs(path, exist_ok=True)
    return path


async def save_uploaded_pdf(file: UploadFile) -> tuple[str, int]:
    storage_dir = ensure_storage_dir()
    ext = os.path.splitext(file.filename or "book.pdf")[1] or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(storage_dir, filename)

    content = await file.read()
    with open(abs_path, "wb") as f:
        f.write(content)

    return abs_path, len(content)


async def download_cover_image(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""

    cover_dir = os.path.join(settings.UPLOAD_DIR, "covers")
    os.makedirs(cover_dir, exist_ok=True)

    suffix = os.path.splitext(parsed.path)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix[:5]}"
    abs_path = os.path.join(cover_dir, filename)

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return ""
            with open(abs_path, "wb") as f:
                f.write(resp.content)
    except Exception:
        return ""

    # Keep relative path usable by frontend static mount.
    return f"/uploads/covers/{filename}"
