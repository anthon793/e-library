from __future__ import annotations

import httpx

from app.utils.rate_limiter import rate_limiter


BASE_URL = "https://openstax.org/api/books"


async def search_openstax(query: str, limit: int = 10) -> list[dict]:
    await rate_limiter.throttle("openstax")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(BASE_URL)
        if response.status_code != 200:
            return []
        payload = response.json()

    books = payload.get("items") or payload if isinstance(payload, list) else []
    results: list[dict] = []
    q = query.lower()

    for item in books:
        title = str(item.get("title", ""))
        if q not in title.lower():
            continue

        links = []
        if item.get("high_resolution_pdf_url"):
            links.append(item["high_resolution_pdf_url"])
        if item.get("pdf_url"):
            links.append(item["pdf_url"])

        results.append(
            {
                "title": title or "Unknown Title",
                "author": item.get("authors", "OpenStax"),
                "description": item.get("description", "") or "",
                "publisher": "OpenStax",
                "published_year": str(item.get("publish_date", ""))[:4],
                "category": item.get("subject_category", "") or "",
                "cover_image": item.get("cover_url", "") or "",
                "possible_download_links": links,
                "source": "OpenStax",
            }
        )

        if len(results) >= limit:
            break

    return results
