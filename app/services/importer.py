from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import crud
from app.models.hybrid_book import HybridBook
from app.services.category_policy import normalize_category
from app.services.doab import search_doab
from app.services.google_books import search_google_books
from app.services.gutenberg import search_gutenberg
from app.services.open_library_hybrid import search_open_library_hybrid
from app.services.openstax import search_openstax
from app.services.pdf_validator import validate_pdf_link
from app.utils.file_storage import download_cover_image
from app.utils.link_extractor import extract_candidate_links, pick_pdf_like_links

logger = logging.getLogger("hybrid_importer")


async def _run_source(name: str, coro):
    try:
        return await coro
    except Exception as exc:  # defensive per-source isolation
        logger.warning("source_failed name=%s err=%s", name, exc)
        return []


async def fetch_external_metadata(query: str, max_results_per_source: int) -> list[dict]:
    tasks = [
        _run_source("google_books", search_google_books(query, max_results_per_source)),
        _run_source("open_library", search_open_library_hybrid(query, max_results_per_source)),
        _run_source("doab", search_doab(query, max_results_per_source)),
        _run_source("openstax", search_openstax(query, max_results_per_source)),
        _run_source("gutenberg", search_gutenberg(query, max_results_per_source)),
    ]
    groups = await asyncio.gather(*tasks)
    merged: list[dict] = []
    for group in groups:
        merged.extend(group)
    return merged


async def import_verified_books(
    db: Session,
    *,
    query: str,
    category: str,
    max_results_per_source: int,
) -> tuple[int, int, list[str]]:
    checked_count = 0
    imported_count = 0
    errors: list[str] = []

    normalized_category = normalize_category(category)
    if not normalized_category:
        return 0, 0, ["invalid_category"]

    raw_books = await fetch_external_metadata(query, max_results_per_source)

    for candidate in raw_books:
        links = extract_candidate_links(candidate)
        links = pick_pdf_like_links(links) or links

        validated_link = ""
        file_size = 0

        for link in links:
            checked_count += 1
            result = await validate_pdf_link(link)
            if result.is_valid:
                validated_link = link
                file_size = result.file_size
                break

        if not validated_link:
            continue

        title = candidate.get("title", "Unknown Title")
        author = candidate.get("author", "Unknown Author")
        preview_link = candidate.get("preview_link", "") or ""

        existing = crud.get_duplicate(db, title=title, author=author, download_link=validated_link)
        if existing:
            continue

        try:
            cover = candidate.get("cover_image", "") or ""
            local_cover = await download_cover_image(cover)
            crud.create_hybrid_book(
                db,
                title=title,
                author=author,
                description=candidate.get("description", "") or "No description provided.",
                category=normalized_category,
                cover_image=local_cover or cover,
                preview_link=preview_link,
                download_link=validated_link,
                source=candidate.get("source", "Unknown"),
                is_verified=True,
                file_size=file_size,
                publisher=candidate.get("publisher", ""),
                published_year=candidate.get("published_year", ""),
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
