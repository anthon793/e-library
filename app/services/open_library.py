import httpx
from typing import Optional

from app.config import settings


async def search_books(query: str, limit: int = 20) -> list[dict]:
    """Search Open Library for books matching the query."""
    url = f"{settings.OPEN_LIBRARY_BASE_URL}/search.json"
    params = {
        "q": query,
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year,cover_i,edition_count,subject",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return []
        data = response.json()

    results = []
    for doc in data.get("docs", []):
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
        work_key = doc.get("key", "")

        results.append({
            "api_id": work_key,
            "title": doc.get("title", "Unknown Title"),
            "author": ", ".join(doc.get("author_name", ["Unknown Author"])),
            "description": "",
            "cover_image": cover_url,
            "view_link": f"https://openlibrary.org{work_key}",
            "first_publish_year": doc.get("first_publish_year", ""),
            "subjects": doc.get("subject", [])[:5],
            "source": "open_library",
        })

    return results


async def get_book_details(work_key: str) -> Optional[dict]:
    """Get detailed info about a specific work from Open Library."""
    # Normalize key
    if not work_key.startswith("/works/"):
        work_key = f"/works/{work_key}"

    url = f"{settings.OPEN_LIBRARY_BASE_URL}{work_key}.json"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url)
        if response.status_code != 200:
            return None
        data = response.json()

    # Get description
    description = ""
    desc_field = data.get("description", "")
    if isinstance(desc_field, dict):
        description = desc_field.get("value", "")
    elif isinstance(desc_field, str):
        description = desc_field

    # Get cover
    covers = data.get("covers", [])
    cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg" if covers else ""

    # Get authors
    authors = []
    for author_ref in data.get("authors", []):
        author_key = author_ref.get("author", {}).get("key", "")
        if author_key:
            async with httpx.AsyncClient(timeout=10.0) as client:
                author_resp = await client.get(f"{settings.OPEN_LIBRARY_BASE_URL}{author_key}.json")
                if author_resp.status_code == 200:
                    author_data = author_resp.json()
                    authors.append(author_data.get("name", "Unknown"))

    return {
        "api_id": work_key,
        "title": data.get("title", "Unknown Title"),
        "author": ", ".join(authors) if authors else "Unknown Author",
        "description": description,
        "cover_image": cover_url,
        "view_link": f"https://openlibrary.org{work_key}",
        "source": "open_library",
        "subjects": [s for s in data.get("subjects", [])[:5]] if data.get("subjects") else [],
    }
