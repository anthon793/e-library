from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_lecturer
from app.models.book import Book, BookType
from app.models.user import User
from app.services import book_service, internet_archive

router = APIRouter(prefix="/archive", tags=["Internet Archive"])


@router.get("/search")
async def search_archive_books(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100)):
    try:
        return await internet_archive.search_books(query=q, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Internet Archive search failed: {exc}") from exc


@router.get("/book/{archive_id}")
async def get_archive_book(archive_id: str):
    try:
        details = await internet_archive.get_book_details(archive_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch archive metadata: {exc}") from exc

    if not details:
        raise HTTPException(status_code=404, detail="Archive book not found")

    details["has_pdf"] = bool(details.get("download_link"))
    return details


@router.post("/import/{archive_id}")
async def import_archive_book(
    archive_id: str,
    category_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    category = book_service.get_allowed_category(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Select a valid category: cybersecurity, data science, or AI")

    existing = db.query(Book).filter(Book.archive_id == archive_id, Book.book_type == BookType.archive).first()
    if existing:
        raise HTTPException(status_code=409, detail="This Internet Archive book has already been imported")

    try:
        details = await internet_archive.get_book_details(archive_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch archive metadata: {exc}") from exc

    if not details:
        raise HTTPException(status_code=404, detail="Archive book not found")

    if not details.get("download_link"):
        raise HTTPException(status_code=400, detail="No publicly accessible PDF is available for this archive book")

    book = book_service.create_book(
        db,
        title=details.get("title") or "Untitled",
        author=details.get("author") or "Unknown Author",
        description=details.get("description") or "",
        category_id=category.id,
        cover_image=details.get("cover_image") or "",
        book_type=BookType.archive,
        preview_link=details.get("preview_link") or "",
        view_link=details.get("download_link") or "",
        download_link=details.get("download_link") or "",
        source="Internet Archive",
        archive_id=archive_id,
        api_id=archive_id,
        added_by=current_user.id,
    )

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "category_id": book.category_id,
        "cover_image": book.cover_image,
        "book_type": book.book_type.value,
        "preview_link": book.preview_link,
        "view_link": book.view_link,
        "download_link": book.download_link,
        "archive_id": book.archive_id,
        "source": book.source,
        "created_at": str(book.created_at),
    }
