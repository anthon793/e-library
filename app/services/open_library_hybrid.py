from __future__ import annotations

import httpx

from app.utils.rate_limiter import rate_limiter


BASE_URL = "https://openlibrary.org/search.json"


def _cover_url(cover_id: int | None) -> str:
    if not cover_id:
        return ""
    return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"


async def search_open_library_hybrid(query: str, limit: int = 10) -> list[dict]:
    await rate_limiter.throttle("open_library")
    params = {
        "q": query,
        "limit": limit,
        "fields": "title,author_name,first_publish_year,cover_i,ia,ebook_access",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(BASE_URL, params=params)
        if response.status_code != 200:
            return []
        payload = response.json()

    results = []
    for doc in payload.get("docs", []):
        ia_ids = doc.get("ia", []) or []
        links = []
        for ia_id in ia_ids[:3]:
            links.append(f"https://archive.org/download/{ia_id}/{ia_id}.pdf")

        results.append(
            {
                "title": doc.get("title", "Unknown Title"),
                "author": ", ".join(doc.get("author_name", ["Unknown Author"])),
                "description": "",
                "publisher": "",
                "published_year": str(doc.get("first_publish_year", "")),
                "category": "",
                "cover_image": _cover_url(doc.get("cover_i")),
                "possible_download_links": links,
                "source": "Open Library",
            }
        )

    return results
