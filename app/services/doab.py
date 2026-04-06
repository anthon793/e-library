from __future__ import annotations

import httpx

from app.utils.rate_limiter import rate_limiter


BASE_URL = "https://directory.doabooks.org/api/search"


async def search_doab(query: str, limit: int = 10) -> list[dict]:
    await rate_limiter.throttle("doab")
    # DOAB API has evolving response shape; keep parser defensive.
    params = {"query": query, "pageSize": limit}

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(BASE_URL, params=params)
        if response.status_code != 200:
            return []
        payload = response.json()

    items = payload.get("results") or payload.get("items") or []
    results: list[dict] = []

    for item in items:
        links = []
        for key in ("pdf", "url", "download", "fullTextUrl"):
            value = item.get(key)
            if value:
                links.append(str(value))

        results.append(
            {
                "title": item.get("title", "Unknown Title"),
                "author": ", ".join(item.get("authors", [])) if isinstance(item.get("authors"), list) else str(item.get("authors", "Unknown Author")),
                "description": item.get("description", "") or "",
                "publisher": item.get("publisher", "") or "",
                "published_year": str(item.get("year", "")),
                "category": item.get("subject", "") or "",
                "cover_image": item.get("cover", "") or "",
                "possible_download_links": links,
                "source": "DOAB",
            }
        )

    return results
