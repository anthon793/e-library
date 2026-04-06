import os
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services import book_service

router = APIRouter(prefix="/legacy/books", tags=["Book Access Gateway"])


@router.get("/{book_id}/view")
def view_book_gateway(book_id: int, db: Session = Depends(get_db)):
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


@router.get("/{book_id}/download")
def download_book_gateway(book_id: int, db: Session = Depends(get_db)):
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

    if book.book_type.value == "archive" and book.download_link:
        book_service.record_download(db, book_id)
        encoded_url = quote_plus(book.download_link)
        return RedirectResponse(url=f"/pdf/proxy?url={encoded_url}&download=1", status_code=307)

    if book.download_link:
        book_service.record_download(db, book_id)
        return RedirectResponse(url=book.download_link, status_code=307)

    if book.view_link:
        book_service.record_download(db, book_id)
        return RedirectResponse(url=book.view_link, status_code=307)

    raise HTTPException(status_code=404, detail="No downloadable file available")
