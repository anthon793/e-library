from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

router = APIRouter(prefix="/pdf", tags=["PDF Proxy"])


def _is_allowed_archive_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    host = hostname.lower()
    return host == "archive.org" or host.endswith(".archive.org")


@router.get("/proxy")
async def proxy_pdf(
    request: Request,
    url: str = Query(..., description="Internet Archive PDF URL"),
    download: int = Query(0, ge=0, le=1),
):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Invalid URL scheme")

    if not _is_allowed_archive_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="Only archive.org PDF URLs are allowed")

    forward_headers = {}
    if request.headers.get("range"):
        forward_headers["Range"] = request.headers["range"]
    forward_headers["User-Agent"] = "Academic-E-Library/1.0"
    forward_headers["Accept"] = "application/pdf,*/*"
    forward_headers["Referer"] = "https://archive.org/"

    timeout = httpx.Timeout(timeout=60.0, connect=20.0)
    client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    try:
        upstream_request = client.build_request("GET", url, headers=forward_headers)
        upstream_response = await client.send(upstream_request, stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"Failed to fetch PDF from Internet Archive: {exc}") from exc

    if upstream_response.status_code >= 400:
        await upstream_response.aclose()
        await client.aclose()
        raise HTTPException(status_code=upstream_response.status_code, detail="Unable to retrieve PDF from source")

    headers = {}
    for header in ("content-length", "content-range", "accept-ranges", "cache-control", "etag", "last-modified"):
        value = upstream_response.headers.get(header)
        if value:
            headers[header] = value

    content_disposition = "attachment" if download else "inline"
    headers["Content-Disposition"] = f"{content_disposition}; filename=archive-book.pdf"

    media_type = upstream_response.headers.get("content-type") or "application/pdf"

    async def _close_upstream() -> None:
        await upstream_response.aclose()
        await client.aclose()

    return StreamingResponse(
        upstream_response.aiter_bytes(),
        status_code=upstream_response.status_code,
        headers=headers,
        media_type=media_type,
        background=BackgroundTask(_close_upstream),
    )
