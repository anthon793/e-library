from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

ARCHIVE_ADVANCED_SEARCH_URL = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA_URL = "https://archive.org/metadata"
ARCHIVE_DETAILS_URL = "https://archive.org/details"
ARCHIVE_COVER_URL = "https://archive.org/services/img"
ARCHIVE_DOWNLOAD_URL = "https://archive.org/download"


def _normalize_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    if isinstance(value, dict):
        return str(value.get("value", ""))
    return str(value or "")


def _extract_author(doc: dict[str, Any]) -> str:
    author = doc.get("creator")
    text = _normalize_text(author).strip()
    return text or "Unknown Author"


def _extract_description(doc: dict[str, Any]) -> str:
    return _normalize_text(doc.get("description", "")).strip()


def _extract_formats(doc: dict[str, Any]) -> list[str]:
    formats = doc.get("format", [])
    if isinstance(formats, str):
        return [formats]
    if isinstance(formats, list):
        return [str(fmt) for fmt in formats if fmt]
    return []


def _build_cover_url(identifier: str) -> str:
    return f"{ARCHIVE_COVER_URL}/{identifier}"


def _build_preview_url(identifier: str) -> str:
    return f"{ARCHIVE_DETAILS_URL}/{identifier}"


def _build_download_url(identifier: str, file_name: str) -> str:
    return f"{ARCHIVE_DOWNLOAD_URL}/{identifier}/{quote(file_name)}"


async def _is_public_pdf(url: str) -> bool:
    headers = {
        "User-Agent": "Academic-E-Library/1.0",
        "Accept": "application/pdf,*/*",
        "Referer": "https://archive.org/",
    }
    timeout = httpx.Timeout(timeout=15.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            head_resp = await client.head(url, headers=headers)
            if head_resp.status_code < 400:
                return True
        except httpx.HTTPError:
            pass

        try:
            get_resp = await client.get(url, headers={**headers, "Range": "bytes=0-1"})
            return get_resp.status_code in (200, 206)
        except httpx.HTTPError:
            return False


def _pick_pdf_file(files: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not files:
        return None

    # Prefer the explicit text PDF variant when present.
    for file_info in files:
        fmt = str(file_info.get("format", "")).lower()
        name = str(file_info.get("name", "")).lower()
        if "text pdf" in fmt and name.endswith(".pdf"):
            return file_info

    for file_info in files:
        name = str(file_info.get("name", "")).lower()
        if name.endswith(".pdf"):
            return file_info

    return None


async def search_books(query: str, limit: int = 20, page: int = 1) -> list[dict[str, Any]]:
    params = {
        "q": f"({query}) AND mediatype:texts",
        "fl[]": ["identifier", "title", "creator", "description", "format", "mediatype"],
        "rows": max(1, min(limit, 100)),
        "page": max(1, page),
        "output": "json",
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(ARCHIVE_ADVANCED_SEARCH_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    docs = payload.get("response", {}).get("docs", [])
    results: list[dict[str, Any]] = []

    for doc in docs:
        identifier = str(doc.get("identifier", "")).strip()
        if not identifier:
            continue

        formats = _extract_formats(doc)
        results.append(
            {
                "archive_id": identifier,
                "title": str(doc.get("title") or "Unknown Title"),
                "author": _extract_author(doc),
                "description": _extract_description(doc),
                "cover_image": _build_cover_url(identifier),
                "available_formats": formats,
                "preview_link": _build_preview_url(identifier),
                "source": "Internet Archive",
            }
        )

    return results


async def get_book_details(archive_id: str) -> dict[str, Any] | None:
    archive_id = archive_id.strip()
    if not archive_id:
        return None

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(f"{ARCHIVE_METADATA_URL}/{archive_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()

    metadata = payload.get("metadata", {}) or {}
    files = payload.get("files", []) or []
    is_restricted = str(metadata.get("access-restricted-item", "")).strip().lower() in {"true", "1", "yes"}

    pdf_file = _pick_pdf_file(files)
    if not pdf_file or is_restricted:
        download_link = ""
    else:
        candidate_link = _build_download_url(archive_id, str(pdf_file.get("name", "")))
        download_link = candidate_link if await _is_public_pdf(candidate_link) else ""

    all_formats = []
    for file_info in files:
        fmt = str(file_info.get("format", "")).strip()
        if fmt:
            all_formats.append(fmt)

    title = _normalize_text(metadata.get("title")).strip() or "Unknown Title"
    author = _normalize_text(metadata.get("creator")).strip() or "Unknown Author"
    description = _normalize_text(metadata.get("description")).strip()

    return {
        "archive_id": archive_id,
        "title": title,
        "author": author,
        "description": description,
        "cover_image": _build_cover_url(archive_id),
        "available_formats": sorted(set(all_formats)),
        "preview_link": _build_preview_url(archive_id),
        "download_link": download_link,
        "source": "Internet Archive",
    }
