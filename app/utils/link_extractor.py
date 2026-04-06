from __future__ import annotations

from collections.abc import Iterable


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(v) for v in value if v]
    return []


def extract_candidate_links(payload: dict) -> list[str]:
    candidates: list[str] = []

    keys = [
        "download_url",
        "pdf_url",
        "access_url",
        "read_url",
        "download_link",
        "full_text_url",
        "url",
        "possible_download_links",
    ]
    for key in keys:
        value = payload.get(key)
        candidates.extend(_as_list(value))

    for key in ("formats", "links", "resources"):
        value = payload.get(key)
        for item in _as_list(value):
            candidates.append(item)

    cleaned = []
    seen = set()
    for link in candidates:
        normalized = str(link).strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)

    return cleaned


def pick_pdf_like_links(links: list[str]) -> list[str]:
    scored = []
    for link in links:
        lowered = link.lower()
        score = 0
        if lowered.endswith(".pdf"):
            score += 3
        if "pdf" in lowered:
            score += 2
        if any(k in lowered for k in ("download", "files", "content", "book")):
            score += 1
        scored.append((score, link))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored if item[0] > 0]
