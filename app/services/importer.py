from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import crud
from app.models.hybrid_book import HybridBook
from app.services.category_policy import normalize_category
from app.services.google_books import search_google_books

logger = logging.getLogger("hybrid_importer")


async def fetch_google_metadata(query: str, max_results_per_source: int, field: str) -> list[dict]:
    try:
        return await search_google_books(
            query,
            max_results=max_results_per_source,
            field=field,
            pdf_only=False,
        )
    except Exception as exc:
        logger.warning("google_books_failed err=%s", exc)
        return []


async def import_verified_books(
    db: Session,
    *,
    query: str,
    category: str,
    field: str,
    max_results_per_source: int,
) -> tuple[int, int, list[str]]:
    checked_count = 0
    imported_count = 0
    errors: list[str] = []

    normalized_category = normalize_category(category)
    if not normalized_category:
        return 0, 0, ["invalid_category"]

    raw_books = await fetch_google_metadata(query, max_results_per_source, field)

    for candidate in raw_books:
        checked_count += 1

        if not candidate.get("embeddable") and not candidate.get("preview_available"):
            continue

        title = candidate.get("title", "Unknown Title")
        author = candidate.get("author", "Unknown Author")
        preview_link = candidate.get("preview_link", "") or candidate.get("viewer_link", "") or ""
        download_link = preview_link or candidate.get("viewer_link", "") or candidate.get("info_link", "") or ""
        file_size = 0

        existing = crud.get_duplicate(db, title=title, author=author, download_link=download_link)
        if existing:
            continue

        try:
            crud.create_hybrid_book(
                db,
                title=title,
                author=author,
                description=candidate.get("description", "") or "No description provided.",
                category=normalized_category,
                cover_image=candidate.get("cover_image", "") or candidate.get("thumbnail", "") or "",
                preview_link=preview_link,
                download_link=download_link,
                source=candidate.get("source", "Google Books"),
                is_verified=bool(candidate.get("embeddable") or candidate.get("preview_available")),
                file_size=file_size,
                publisher=candidate.get("publisher", ""),
                published_year=candidate.get("published_date", "") or candidate.get("published_year", ""),
                created_at=datetime.now(timezone.utc),
                last_checked=datetime.now(timezone.utc),
            )
            imported_count += 1
        except Exception as exc:
            db.rollback()
            msg = f"store_failed:{title}:{exc}"
            logger.warning(msg)
            errors.append(msg)

    return imported_count, checked_count, errors


def list_books_with_filters(db: Session, *, skip: int, limit: int, category: str | None, author: str | None, source: str | None):
    return crud.list_hybrid_books(db, skip=skip, limit=limit, category=category, author=author, source=source)


def search_local_books(db: Session, *, q: str, skip: int, limit: int):
    return crud.search_hybrid_books(db, q=q, skip=skip, limit=limit)


def get_book_or_404(db: Session, book_id: int) -> HybridBook | None:
    return db.query(HybridBook).filter(HybridBook.id == book_id).first()
