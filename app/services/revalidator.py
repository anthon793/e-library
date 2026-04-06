from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.hybrid_book import HybridBook
from app.services.pdf_validator import validate_pdf_link


async def revalidate_links(db: Session, limit: int = 100) -> dict:
    books = db.query(HybridBook).order_by(HybridBook.last_checked.asc()).limit(limit).all()

    valid = 0
    invalid = 0
    for book in books:
        if not book.download_link:
            book.is_verified = False
            book.last_checked = datetime.now(timezone.utc)
            invalid += 1
            continue

        result = await validate_pdf_link(book.download_link)
        book.is_verified = result.is_valid
        book.file_size = result.file_size if result.is_valid else 0
        book.last_checked = result.checked_at
        if result.is_valid:
            valid += 1
        else:
            invalid += 1

    db.commit()
    return {"checked": len(books), "valid": valid, "invalid": invalid}
