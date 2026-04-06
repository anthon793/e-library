from __future__ import annotations

import httpx

from app.utils.rate_limiter import rate_limiter


BASE_URL = "https://gutendex.com/books"


async def search_gutenberg(query: str, limit: int = 10) -> list[dict]:
    await rate_limiter.throttle("gutenberg")
    params = {"search": query}

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(BASE_URL, params=params)
        if response.status_code != 200:
            return []
        payload = response.json()

    results = []
    for item in payload.get("results", [])[:limit]:
        formats = item.get("formats", {})
        links = []
        for key, value in formats.items():
            if "pdf" in key.lower() and isinstance(value, str):
                links.append(value)

        results.append(
            {
                "title": item.get("title", "Unknown Title"),
                "author": ", ".join([a.get("name", "Unknown Author") for a in item.get("authors", [])]) or "Unknown Author",
                "description": "",
                "publisher": "Project Gutenberg",
                "published_year": "",
                "category": ", ".join(item.get("subjects", [])[:3]),
                "cover_image": (formats.get("image/jpeg") or ""),
                "possible_download_links": links,
                "source": "Project Gutenberg",
            }
        )

    return results
