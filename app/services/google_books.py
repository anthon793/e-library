from __future__ import annotations

from typing import Iterable

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.google_book import GoogleBook
from app.utils.rate_limiter import rate_limiter


BASE_URL = "https://www.googleapis.com/books/v1/volumes"
ALLOWED_VIEWABILITY = {"PARTIAL", "ALL_PAGES", "VIEW_PARTIAL"}


def _join_values(values: Iterable[str] | None) -> str:
    return ", ".join([value for value in (values or []) if value])


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_query(query: str, field: str = "all") -> str:
    cleaned = (query or "").strip()
    if not cleaned:
        return ""

    field = (field or "all").strip().lower()
    if field == "title":
        return f'intitle:"{cleaned}"'
    if field == "author":
        return f'inauthor:"{cleaned}"'
    if field == "isbn":
        return f"isbn:{cleaned}"
    if field == "subject":
        return f'subject:"{cleaned}"'
    return cleaned


def _extract_volume_id(item: dict) -> str:
    volume_id = item.get("id") or ""
    if volume_id:
        return volume_id

    self_link = item.get("selfLink") or ""
    if "/volumes/" in self_link:
        return self_link.rsplit("/volumes/", 1)[-1]

    return ""


def _build_viewer_link(volume_id: str) -> str:
    return f"https://books.google.com/books?id={volume_id}&output=embed"


def _book_to_dict(book: GoogleBook) -> dict:
    categories = _split_values(book.categories)
    return {
        "id": book.id,
        "volume_id": book.volume_id,
        "title": book.title,
        "authors": _split_values(book.authors),
        "author": book.authors,
        "description": book.description,
        "publisher": book.publisher,
        "published_date": book.published_date,
        "categories": categories,
        "category_name": categories[0] if categories else "Google Books",
        "thumbnail": book.thumbnail,
        "cover_image": book.thumbnail,
        "preview_link": book.preview_link,
        "viewer_link": book.viewer_link,
        "info_link": book.info_link,
        "canonical_link": book.canonical_link,
        "viewability": book.viewability,
        "preview_available": bool(book.preview_available),
        "embeddable": bool(book.preview_available),
        "pdf_viewable": False,
        "language": book.language,
        "page_count": book.page_count,
        "isbn_10": book.isbn_10,
        "isbn_13": book.isbn_13,
        "source": "Google Books",
        "book_type": "google_books",
        "download_count": 0,
        "cached_at": book.cached_at.isoformat() if book.cached_at else None,
        "updated_at": book.updated_at.isoformat() if book.updated_at else None,
    }


def to_embedded_reader_payload(book: GoogleBook | dict) -> dict:
    data = _book_to_dict(book) if isinstance(book, GoogleBook) else dict(book)
    embeddable = bool(data.get("embeddable", data.get("preview_available")))
    pdf_viewable = bool(data.get("pdf_viewable", data.get("preview_available")))
    return {
        "title": data.get("title") or "Unknown Title",
        "authors": data.get("authors") or [],
        "thumbnail": data.get("thumbnail") or data.get("cover_image") or "",
        "description": data.get("description") or "",
        "previewLink": data.get("preview_link") or "",
        "volumeId": data.get("volume_id") or "",
        "embeddable": embeddable,
        "pdfViewable": pdf_viewable,
        "viewability": data.get("viewability") or "",
    }


def _parse_google_item(item: dict) -> dict:
    info = item.get("volumeInfo") or {}
    access = item.get("accessInfo") or {}
    identifiers = info.get("industryIdentifiers") or []
    isbn_10 = ""
    isbn_13 = ""
    for ident in identifiers:
        if ident.get("type") == "ISBN_10" and not isbn_10:
            isbn_10 = ident.get("identifier", "")
        if ident.get("type") == "ISBN_13" and not isbn_13:
            isbn_13 = ident.get("identifier", "")

    volume_id = _extract_volume_id(item)
    preview_link = info.get("previewLink") or info.get("canonicalVolumeLink") or ""
    viewer_link = _build_viewer_link(volume_id) if volume_id else preview_link
    viewability = access.get("viewability") or ""
    embeddable = bool(access.get("embeddable"))
    pdf_available = bool((access.get("pdf") or {}).get("isAvailable"))
    preview_available = embeddable

    return {
        "volume_id": volume_id,
        "title": info.get("title") or "Unknown Title",
        "authors": _join_values(info.get("authors")),
        "description": info.get("description") or "",
        "publisher": info.get("publisher") or "",
        "published_date": info.get("publishedDate") or "",
        "categories": _join_values(info.get("categories")),
        "thumbnail": (info.get("imageLinks") or {}).get("thumbnail") or (info.get("imageLinks") or {}).get("smallThumbnail") or "",
        "preview_link": preview_link,
        "viewer_link": viewer_link,
        "info_link": info.get("infoLink") or info.get("canonicalVolumeLink") or preview_link,
        "canonical_link": info.get("canonicalVolumeLink") or "",
        "viewability": viewability,
        "embeddable": embeddable,
        "pdf_viewable": pdf_available,
        "preview_available": preview_available,
        "language": info.get("language") or "",
        "page_count": int(info.get("pageCount") or 0),
        "isbn_10": isbn_10,
        "isbn_13": isbn_13,
    }


def _upsert_google_book(db: Session, payload: dict) -> GoogleBook:
    book = db.query(GoogleBook).filter(GoogleBook.volume_id == payload["volume_id"]).first()
    if not book:
        book = GoogleBook(volume_id=payload["volume_id"])
        db.add(book)

    book.title = payload["title"]
    book.authors = payload["authors"]
    book.description = payload["description"]
    book.publisher = payload["publisher"]
    book.published_date = payload["published_date"]
    book.categories = payload["categories"]
    book.thumbnail = payload["thumbnail"]
    book.preview_link = payload["preview_link"]
    book.viewer_link = payload["viewer_link"]
    book.info_link = payload["info_link"]
    book.canonical_link = payload["canonical_link"]
    book.viewability = payload["viewability"]
    book.preview_available = bool(payload["preview_available"])
    book.language = payload["language"]
    book.page_count = payload["page_count"]
    book.isbn_10 = payload["isbn_10"]
    book.isbn_13 = payload["isbn_13"]
    return book


def _search_cached_google_books(db: Session, query: str, field: str, max_results: int) -> list[GoogleBook]:
    pattern = f"%{query.strip()}%"
    q = db.query(GoogleBook)

    if field == "title":
        q = q.filter(GoogleBook.title.ilike(pattern))
    elif field == "author":
        q = q.filter(GoogleBook.authors.ilike(pattern))
    elif field == "isbn":
        q = q.filter(or_(GoogleBook.isbn_10.ilike(pattern), GoogleBook.isbn_13.ilike(pattern), GoogleBook.volume_id.ilike(pattern)))
    elif field == "subject":
        q = q.filter(GoogleBook.categories.ilike(pattern))
    else:
        q = q.filter(
            or_(
                GoogleBook.title.ilike(pattern),
                GoogleBook.authors.ilike(pattern),
                GoogleBook.description.ilike(pattern),
                GoogleBook.categories.ilike(pattern),
                GoogleBook.publisher.ilike(pattern),
                GoogleBook.volume_id.ilike(pattern),
                GoogleBook.isbn_10.ilike(pattern),
                GoogleBook.isbn_13.ilike(pattern),
            )
        )

    return q.order_by(GoogleBook.updated_at.desc()).limit(max_results).all()


async def _fetch_google_books(query: str, max_results: int = 10, *, field: str = "all", start_index: int = 0) -> list[dict]:
    await rate_limiter.throttle("google_books")
    params = {
        "q": _build_query(query, field),
        "maxResults": max_results,
        "startIndex": start_index,
        "printType": "books",
        "projection": "full",
    }
    if settings.GOOGLE_BOOKS_API_KEY:
        params["key"] = settings.GOOGLE_BOOKS_API_KEY

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(BASE_URL, params=params)

    if response.status_code == 429:
        raise RuntimeError("Google Books API rate limit reached")
    if response.status_code != 200:
        raise RuntimeError(f"Google Books API returned HTTP {response.status_code}")

    payload = response.json()
    items = payload.get("items") or []
    return [_parse_google_item(item) for item in items]


async def search_google_books(
    query: str,
    max_results: int = 10,
    *,
    field: str = "all",
    pdf_only: bool = True,
    db: Session | None = None,
    start_index: int = 0,
) -> list[dict]:
    normalized_field = (field or "all").strip().lower()

    cached_books: list[GoogleBook] = []
    if db is not None and not pdf_only:
        cached_books = _search_cached_google_books(db, query, normalized_field, max_results)

    remote_payloads: list[dict] = []
    try:
        remote_payloads = await _fetch_google_books(query, max_results=max_results, field=normalized_field, start_index=start_index)
    except RuntimeError:
        remote_payloads = []

    if db is not None and remote_payloads:
        for payload in remote_payloads:
            _upsert_google_book(db, payload)
        db.commit()

    results_by_volume: dict[str, dict] = {}
    for book in cached_books:
        results_by_volume[book.volume_id] = _book_to_dict(book)

    if db is not None:
        refreshed_books = _search_cached_google_books(db, query, normalized_field, max_results)
        for book in refreshed_books:
            results_by_volume[book.volume_id] = _book_to_dict(book)
    else:
        for payload in remote_payloads:
            categories = _split_values(payload["categories"])
            results_by_volume[payload["volume_id"]] = {
                "id": payload["volume_id"],
                "volume_id": payload["volume_id"],
                "title": payload["title"],
                "authors": _split_values(payload["authors"]),
                "author": payload["authors"],
                "description": payload["description"],
                "publisher": payload["publisher"],
                "published_date": payload["published_date"],
                "categories": categories,
                "category_name": categories[0] if categories else "Google Books",
                "thumbnail": payload["thumbnail"],
                "cover_image": payload["thumbnail"],
                "preview_link": payload["preview_link"],
                "viewer_link": payload["viewer_link"],
                "info_link": payload["info_link"],
                "canonical_link": payload["canonical_link"],
                "viewability": payload["viewability"],
                "embeddable": bool(payload.get("embeddable", payload.get("preview_available"))),
                "pdf_viewable": bool(payload.get("pdf_viewable", False)),
                "preview_available": bool(payload["preview_available"]),
                "language": payload["language"],
                "page_count": payload["page_count"],
                "isbn_10": payload["isbn_10"],
                "isbn_13": payload["isbn_13"],
                "source": "Google Books",
                "book_type": "google_books",
                "download_count": 0,
            }

    filtered_results = []
    for item in results_by_volume.values():
        is_embeddable = bool(item.get("embeddable", item.get("preview_available")))
        is_pdf_viewable = bool(item.get("pdf_viewable", False))
        if pdf_only:
            if is_embeddable and is_pdf_viewable:
                filtered_results.append(item)
        elif is_embeddable:
            filtered_results.append(item)

    return filtered_results[:max_results]


def get_google_book_by_id(db: Session, book_id: int) -> GoogleBook | None:
    return db.query(GoogleBook).filter(GoogleBook.id == book_id).first()


def get_google_book_by_volume_id(db: Session, volume_id: str) -> GoogleBook | None:
    normalized = (volume_id or "").strip()
    if not normalized:
        return None
    return db.query(GoogleBook).filter(GoogleBook.volume_id == normalized).first()


async def fetch_google_book_volume(volume_id: str, db: Session | None = None) -> dict | None:
    normalized = (volume_id or "").strip()
    if not normalized:
        return None

    await rate_limiter.throttle("google_books")
    params = {}
    if settings.GOOGLE_BOOKS_API_KEY:
        params["key"] = settings.GOOGLE_BOOKS_API_KEY

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{BASE_URL}/{normalized}", params=params)

    if response.status_code in {403, 404}:
        return None
    if response.status_code == 429:
        raise RuntimeError("Google Books API rate limit reached")
    if response.status_code != 200:
        raise RuntimeError(f"Google Books API returned HTTP {response.status_code}")

    payload = _parse_google_item(response.json())
    if db is not None and payload.get("volume_id"):
        _upsert_google_book(db, payload)
        db.commit()
    return payload

