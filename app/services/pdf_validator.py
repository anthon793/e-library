from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx


@dataclass
class ValidationResult:
    is_valid: bool
    file_size: int
    checked_at: datetime
    reason: str = ""


def _is_http_link(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


async def validate_pdf_link(url: str, timeout_seconds: int = 20) -> ValidationResult:
    now = datetime.now(timezone.utc)

    if not _is_http_link(url):
        return ValidationResult(False, 0, now, "invalid_url")

    timeout = httpx.Timeout(timeout=timeout_seconds, connect=10)
    headers = {"User-Agent": "HybridBookBot/1.0", "Accept": "application/pdf,*/*"}

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            head = await client.head(url, headers=headers)
        except httpx.HTTPError as exc:
            return ValidationResult(False, 0, now, f"head_error:{exc}")

        content_type = (head.headers.get("content-type") or "").lower()
        content_length = int(head.headers.get("content-length") or 0)

        if head.status_code < 400 and "application/pdf" in content_type and content_length > 0:
            return ValidationResult(True, content_length, now)

        # Some CDNs serve PDFs as generic binary content; accept likely PDF URLs.
        if (
            head.status_code < 400
            and content_length > 0
            and "application/octet-stream" in content_type
            and url.lower().split("?", 1)[0].endswith(".pdf")
        ):
            return ValidationResult(True, content_length, now)

        # Some hosts block HEAD or omit content headers; probe with a small range GET.
        try:
            probe = await client.get(url, headers={**headers, "Range": "bytes=0-2048"})
        except httpx.HTTPError as exc:
            return ValidationResult(False, 0, now, f"get_error:{exc}")

        probe_type = (probe.headers.get("content-type") or "").lower()
        size = int(probe.headers.get("content-length") or content_length or 0)

        if probe.status_code in (200, 206) and "application/pdf" in probe_type:
            if size <= 0:
                size = max(len(probe.content), 1)
            return ValidationResult(True, size, now)

        # Signature fallback for hosts that return incorrect content-type.
        if probe.status_code in (200, 206) and probe.content.startswith(b"%PDF"):
            if size <= 0:
                size = max(len(probe.content), 1)
            return ValidationResult(True, size, now)

        return ValidationResult(False, 0, now, "not_pdf")
