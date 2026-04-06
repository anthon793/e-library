from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from urllib.parse import quote_plus

from app.dependencies import get_db, get_current_user, get_current_user_optional, require_lecturer
from app.services import book_service
from app.services.google_books import (
    fetch_google_book_volume,
    get_google_book_by_volume_id,
    search_google_books,
    to_embedded_reader_payload,
)
from app.models.user import User
from app.models.book import BookType

router = APIRouter(prefix="/api/books", tags=["Books"])


def _google_search_response(items: list[dict]) -> dict:
    payload = [to_embedded_reader_payload(item) for item in items if bool(item.get("preview_available"))]
    return {
        "total": len(payload),
        "items": payload,
    }


@router.get("")
def list_books(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    books = book_service.get_books(db, skip=skip, limit=limit, category_id=category_id)
    results = []
    for book in books:
        cat_name = book.category.name if book.category else "Uncategorized"
        results.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "description": book.description,
            "category_id": book.category_id,
            "category_name": cat_name,
            "cover_image": book.cover_image,
            "book_type": book.book_type.value,
            "preview_link": book.preview_link,
            "view_link": book.view_link,
            "download_link": book.download_link,
            "file_path": book.file_path,
            "source": book.source,
            "archive_id": book.archive_id,
            "download_count": book.download_count,
            "created_at": str(book.created_at),
        })
    return results


@router.get("/search")
async def search_books_endpoint(
    q: str = Query(""),
    category_id: Optional[int] = None,
    source: str = Query("archive"),
    field: str = Query("all"),
    max_results: int = Query(12, ge=1, le=40),
    pdf_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    if not q:
        return {"total": 0, "items": []} if source.lower() == "google" else []

    if source.lower() == "google":
        items = await search_google_books(q, max_results=max_results, field=field, pdf_only=pdf_only, db=db)
        return {
            "query": q,
            "field": field,
            "pdf_only": pdf_only,
            **_google_search_response(items),
        }

    books = book_service.search_books(db, q=q, category_id=category_id)
    results = []
    for book in books:
        cat_name = book.category.name if book.category else "Uncategorized"
        results.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "description": book.description[:200] if book.description else "",
            "category_id": book.category_id,
            "category_name": cat_name,
            "cover_image": book.cover_image,
            "book_type": book.book_type.value,
            "preview_link": book.preview_link,
            "view_link": book.view_link,
            "download_link": book.download_link,
            "archive_id": book.archive_id,
            "download_count": book.download_count,
        })
    return results


@router.get("/category/{category_id}")
def books_by_category(category_id: int, db: Session = Depends(get_db)):
    books = book_service.get_books(db, category_id=category_id, limit=100)
    results = []
    for book in books:
        cat_name = book.category.name if book.category else "Uncategorized"
        results.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "cover_image": book.cover_image,
            "book_type": book.book_type.value,
            "category_name": cat_name,
            "download_count": book.download_count,
        })
    return results


@router.get("/{book_ref}/viewer")
async def get_book_viewer(
    book_ref: str,
    source: str = Query("google"),
    db: Session = Depends(get_db),
):
    if source.lower() != "google" and book_ref.isdigit():
        raise HTTPException(status_code=404, detail="Viewer endpoint only supports Google Books volume IDs")

    google_book = get_google_book_by_volume_id(db, book_ref)
    if not google_book:
        payload = await fetch_google_book_volume(book_ref, db=db)
        if not payload:
            raise HTTPException(status_code=404, detail="Google Books title not found")
        if not bool(payload.get("preview_available")):
            raise HTTPException(status_code=404, detail="No embeddable PDF-viewable Google Books preview is available for this title")
        return {
            **to_embedded_reader_payload(payload),
            "loadMode": "volumeId",
        }

    serialized = to_embedded_reader_payload(google_book)
    if not serialized["embeddable"]:
        raise HTTPException(status_code=404, detail="No embeddable PDF-viewable Google Books preview is available for this title")

    return {
        **serialized,
        "loadMode": "volumeId",
    }


@router.get("/{book_ref}")
async def get_book(
    book_ref: str,
    source: str = Query("archive"),
    db: Session = Depends(get_db),
):
    if source.lower() == "google" or not book_ref.isdigit():
        google_book = get_google_book_by_volume_id(db, book_ref)
        if not google_book:
            payload = await fetch_google_book_volume(book_ref, db=db)
            if not payload:
                raise HTTPException(status_code=404, detail="Google Books title not found")
            if not bool(payload.get("preview_available")):
                raise HTTPException(status_code=404, detail="Google Books title is not PDF-viewable in the embedded reader")
            return to_embedded_reader_payload(payload)

        serialized = to_embedded_reader_payload(google_book)
        if not serialized["embeddable"]:
            raise HTTPException(status_code=404, detail="Google Books title is not PDF-viewable in the embedded reader")
        return serialized

    book_id = int(book_ref)
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    description = book.description or ""

    # Auto-fetch description from Open Library if empty
    if not description and book.api_id and book.source == "open_library":
        from app.services.seed_books import fetch_book_description
        description = fetch_book_description(book.api_id)
        if description:
            book.description = description
            db.commit()

    cat_name = book.category.name if book.category else "Uncategorized"

    # Build preview / embed URLs for Open Library books
    preview_url = ""
    embed_url = ""
    if book.api_id and book.source == "open_library":
        work_id = book.api_id.replace("/works/", "")
        preview_url = f"https://openlibrary.org{book.api_id}"
        # Open Library's BookReader embed
        embed_url = f"https://openlibrary.org{book.api_id}?mode=embed"

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "description": description,
        "category_id": book.category_id,
        "category_name": cat_name,
        "cover_image": book.cover_image,
        "book_type": book.book_type.value,
        "preview_link": book.preview_link,
        "view_link": book.view_link,
        "download_link": book.download_link,
        "file_path": book.file_path,
        "source": book.source,
        "api_id": book.api_id,
        "archive_id": book.archive_id,
        "download_count": book.download_count,
        "created_at": str(book.created_at),
        "preview_url": preview_url,
        "embed_url": embed_url,
    }


@router.post("/upload")
async def upload_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    category = book_service.get_allowed_category(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Select a valid category: cybersecurity, data science, or AI")

    filepath = await book_service.save_uploaded_file(file)
    book = book_service.create_book(
        db,
        title=title,
        author=author,
        description=description,
        category_id=category.id,
        book_type=BookType.upload,
        file_path=filepath,
        source="upload",
        added_by=current_user.id,
    )
    return {"message": "Book uploaded successfully", "book_id": book.id}


@router.post("/add-drive")
def add_drive_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    drive_link: str = Form(...),
    cover_image: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    category = book_service.get_allowed_category(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Select a valid category: cybersecurity, data science, or AI")

    book = book_service.create_book(
        db,
        title=title,
        author=author,
        description=description,
        category_id=category.id,
        book_type=BookType.drive,
        view_link=drive_link,
        download_link=drive_link,
        cover_image=cover_image,
        source="drive",
        added_by=current_user.id,
    )
    return {"message": "Drive book added successfully", "book_id": book.id}


@router.post("/add-external")
def add_external_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    cover_image: str = Form(""),
    view_link: str = Form(""),
    api_id: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    category = book_service.get_allowed_category(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Select a valid category: cybersecurity, data science, or AI")

    book = book_service.create_book(
        db,
        title=title,
        author=author,
        description=description,
        category_id=category.id,
        book_type=BookType.external,
        view_link=view_link,
        cover_image=cover_image,
        source="open_library",
        api_id=api_id,
        added_by=current_user.id,
    )
    return {"message": "External book added successfully", "book_id": book.id}


@router.put("/{book_id}")
def update_book_endpoint(
    book_id: int,
    title: str = Form(None),
    author: str = Form(None),
    description: str = Form(None),
    category_id: int = Form(None),
    cover_image: str = Form(None),
    view_link: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if author is not None:
        kwargs["author"] = author
    if description is not None:
        kwargs["description"] = description
    if category_id is not None:
        category = book_service.get_allowed_category(db, category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Select a valid category: cybersecurity, data science, or AI")
        kwargs["category_id"] = category.id
    if cover_image is not None:
        kwargs["cover_image"] = cover_image
    if view_link is not None:
        kwargs["view_link"] = view_link

    book = book_service.update_book(db, book_id, **kwargs)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book updated successfully"}


@router.delete("/{book_id}")
def delete_book_endpoint(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    success = book_service.delete_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@router.get("/{book_id}/download")
def download_book(
    book_id: int,
    db: Session = Depends(get_db),
):
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.source == "open_library" or book.book_type.value == "external":
        raise HTTPException(status_code=404, detail="Open Library books are disabled. Use Internet Archive books only.")

    if book.book_type.value == "upload" and book.file_path:
        if not os.path.exists(book.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        book_service.record_download(db, book_id)
        return FileResponse(
            path=book.file_path,
            filename=f"{book.title}.pdf",
            media_type="application/pdf",
        )
    elif book.book_type.value == "archive" and book.download_link:
        book_service.record_download(db, book_id)
        encoded_url = quote_plus(book.download_link)
        return RedirectResponse(url=f"/pdf/proxy?url={encoded_url}&download=1", status_code=307)
    elif book.download_link:
        book_service.record_download(db, book_id)
        return RedirectResponse(url=book.download_link, status_code=307)
    elif book.view_link:
        book_service.record_download(db, book_id)
        return RedirectResponse(url=book.view_link, status_code=307)
    else:
        raise HTTPException(status_code=404, detail="No downloadable file available")


@router.get("/{book_id}/view")
def view_book(
    book_id: int,
    db: Session = Depends(get_db),
):
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.source == "open_library" or book.book_type.value == "external":
        raise HTTPException(status_code=404, detail="Open Library books are disabled. Use Internet Archive books only.")

    if book.book_type.value == "upload" and book.file_path:
        if not os.path.exists(book.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        return FileResponse(
            path=book.file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{book.title}.pdf"'},
        )

    if book.book_type.value == "archive":
        if book.download_link:
            encoded_url = quote_plus(book.download_link)
            return RedirectResponse(url=f"/pdf/proxy?url={encoded_url}", status_code=307)
        raise HTTPException(status_code=404, detail="No PDF available for this archive book")

    target = book.view_link or book.preview_link or book.download_link
    if target:
        return RedirectResponse(url=target, status_code=307)

    raise HTTPException(status_code=404, detail="No viewable resource available")
