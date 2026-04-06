from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.hybrid_book import HybridBook
from app.services.category_policy import normalize_category


def get_duplicate(db: Session, *, title: str, author: str, download_link: str) -> HybridBook | None:
    return (
        db.query(HybridBook)
        .filter(
            or_(
                HybridBook.download_link == download_link,
                (func.lower(HybridBook.title) == title.lower()) & (func.lower(HybridBook.author) == author.lower()),
            )
        )
        .first()
    )


def create_hybrid_book(db: Session, **kwargs) -> HybridBook:
    book = HybridBook(**kwargs)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def list_hybrid_books(
    db: Session,
    *,
    skip: int,
    limit: int,
    category: str | None,
    author: str | None,
    source: str | None,
):
    query = db.query(HybridBook)
    if category:
        normalized_category = normalize_category(category) or category
        query = query.filter(HybridBook.category.ilike(f"%{normalized_category}%"))
    if author:
        query = query.filter(HybridBook.author.ilike(f"%{author}%"))
    if source:
        query = query.filter(HybridBook.source.ilike(f"%{source}%"))

    total = query.count()
    items = query.order_by(HybridBook.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def search_hybrid_books(db: Session, q: str, *, skip: int, limit: int, category: str | None = None):
    query = db.query(HybridBook).filter(
        or_(
            HybridBook.title.ilike(f"%{q}%"),
            HybridBook.author.ilike(f"%{q}%"),
            HybridBook.description.ilike(f"%{q}%"),
            HybridBook.category.ilike(f"%{q}%"),
        )
    )

    if category:
        normalized_category = normalize_category(category) or category
        query = query.filter(HybridBook.category.ilike(f"%{normalized_category}%"))

    total = query.count()
    items = query.order_by(HybridBook.created_at.desc()).offset(skip).limit(limit).all()
    return items, total
