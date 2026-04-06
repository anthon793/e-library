from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_lecturer
from app.services import open_library
from app.services.book_service import create_book, get_allowed_category
from app.models.user import User
from app.models.book import BookType

router = APIRouter(prefix="/api", tags=["External APIs"])


@router.get("/openlibrary/search")
async def search_open_library(q: str = Query(..., min_length=1)):
    """Search books on Open Library."""
    results = await open_library.search_books(q, limit=20)
    return results


@router.post("/import/openlibrary")
async def import_from_open_library(
    api_id: str = Form(...),
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    cover_image: str = Form(""),
    view_link: str = Form(""),
    category_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    """Import a book from Open Library into the local database."""
    category = get_allowed_category(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Select a valid category: cybersecurity, data science, or AI")

    book = create_book(
        db,
        title=title,
        author=author,
        description=description,
        category_id=category.id,
        cover_image=cover_image,
        view_link=view_link,
        book_type=BookType.external,
        source="open_library",
        api_id=api_id,
        added_by=current_user.id,
    )
    return {"message": "Book imported successfully", "book_id": book.id}
