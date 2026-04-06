from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.google_books import get_google_book_by_id, search_google_books, _book_to_dict

router = APIRouter(prefix="/api/google-books", tags=["Google Books"])


@router.get("/search")
async def search_endpoint(
    q: str = Query(..., min_length=1),
    field: str = Query("all"),
    max_results: int = Query(12, ge=1, le=40),
    db: Session = Depends(get_db),
):
    items = await search_google_books(q, max_results=max_results, field=field, db=db)
    return {
        "query": q,
        "field": field,
        "total": len(items),
        "items": items,
    }


@router.get("/{book_id}")
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = get_google_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Google Books title not found")
    return _book_to_dict(book)


@router.get("/{book_id}/viewer")
def get_viewer(book_id: int, db: Session = Depends(get_db)):
    book = get_google_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Google Books title not found")

    if not book.preview_available or not book.viewer_link:
        raise HTTPException(status_code=404, detail="No embeddable Google Books preview is available for this title")

    return {
        "id": book.id,
        "volume_id": book.volume_id,
        "title": book.title,
        "viewer_link": book.viewer_link,
        "preview_link": book.preview_link,
        "preview_available": book.preview_available,
        "viewability": book.viewability,
    }
