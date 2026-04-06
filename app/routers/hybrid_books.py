from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask
import httpx

from app import crud
from app.dependencies import get_db, require_lecturer
from app.models.hybrid_book import HybridBook
from app.models.user import User
from app.schemas.hybrid_book import (
    AutoImportRequest,
    AutoImportResponse,
    HybridBookListResponse,
    HybridBookResponse,
    ImportJobStatus,
    UploadBookResponse,
)
from app.tasks.background_tasks import create_job, get_job, run_auto_import_job
from app.services.category_policy import normalize_category
from app.services.google_books import fetch_google_book_volume
from app.services.revalidator import revalidate_links
from app.utils.file_storage import save_uploaded_pdf

router = APIRouter(prefix="/books", tags=["Hybrid Books"])

DEFAULT_CATEGORY_META = [
    {
        "name": "Cybersecurity",
        "slug": "cybersecurity",
        "description": "Information security, ethical hacking, and network defense",
    },
    {
        "name": "Data Science",
        "slug": "data-science",
        "description": "Data analysis, statistics, and machine learning",
    },
    {
        "name": "Artificial Intelligence",
        "slug": "artificial-intelligence",
        "description": "AI, deep learning, and neural networks",
    },
]


def _is_google_books_source(book: HybridBook) -> bool:
    source = (book.source or "").lower()
    link = (book.preview_link or "") + " " + (book.download_link or "")
    return "google books" in source or "books.google" in link or "play.google.com/books" in link


def _google_embed_url_from_book(book: HybridBook) -> str:
    candidate_links = [book.preview_link or "", book.download_link or ""]
    for link in candidate_links:
        if not link:
            continue
        parsed = urlparse(link)
        volume_id = parse_qs(parsed.query).get("id", [""])[0]
        if not volume_id and parsed.path:
            if parsed.path.startswith("/books"):
                volume_id = parse_qs(parsed.query).get("id", [""])[0]
        if volume_id:
            return f"https://books.google.com/books?id={volume_id}&output=embed"

    return ""


def _extract_google_volume_id(book: HybridBook) -> str:
    candidate_links = [book.preview_link or "", book.download_link or ""]
    for link in candidate_links:
        if not link:
            continue
        parsed = urlparse(link)
        volume_id = parse_qs(parsed.query).get("id", [""])[0]
        if volume_id:
            return volume_id

        if "/volumes/" in parsed.path:
            return parsed.path.rsplit("/volumes/", 1)[-1].split("/")[0]

    return ""


@router.post("/auto-import", response_model=AutoImportResponse)
def auto_import_books(
    payload: AutoImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_lecturer),
):
    normalized_category = normalize_category(payload.category)
    if not normalized_category:
        raise HTTPException(status_code=400, detail="Category must be one of: cybersecurity, data-science, artificial-intelligence")

    normalized_field = (payload.field or "all").strip().lower()
    if normalized_field not in {"all", "title", "author", "isbn", "subject"}:
        raise HTTPException(status_code=400, detail="Field must be one of: all, title, author, isbn, subject")

    job = create_job(payload.query)
    background_tasks.add_task(
        run_auto_import_job,
        job.job_id,
        payload.query,
        normalized_category,
        normalized_field,
        payload.max_results_per_source,
    )
    return AutoImportResponse(job_id=job.job_id, status=job.status, message="Google Books import started")


@router.get("/auto-import/{job_id}", response_model=ImportJobStatus)
def auto_import_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return ImportJobStatus(
        job_id=job.job_id,
        status=job.status,
        query=job.query,
        imported_count=job.imported_count,
        checked_count=job.checked_count,
        errors=job.errors,
    )


@router.get("/verify-import")
async def verify_imported_books(
    category: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    normalized_category = normalize_category(category) or category
    category_slug = str(category).strip().lower().replace("_", "-")

    books = (
        db.query(HybridBook)
        .filter(
            or_(
                HybridBook.category.ilike(f"%{normalized_category}%"),
                HybridBook.category.ilike(f"%{category_slug}%"),
            )
        )
        .filter(HybridBook.source.ilike("%google books%"))
        .order_by(HybridBook.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    working = 0
    missing_identifier = 0
    restricted = 0
    not_found = 0
    errors = 0

    for book in books:
        volume_id = _extract_google_volume_id(book)
        if not volume_id:
            missing_identifier += 1
            results.append({
                "id": book.id,
                "title": book.title,
                "status": "missing_identifier",
                "volume_id": "",
            })
            continue

        try:
            payload = await fetch_google_book_volume(volume_id)
        except Exception:
            errors += 1
            results.append({
                "id": book.id,
                "title": book.title,
                "status": "error",
                "volume_id": volume_id,
            })
            continue

        if not payload:
            not_found += 1
            results.append({
                "id": book.id,
                "title": book.title,
                "status": "not_found",
                "volume_id": volume_id,
            })
            continue

        if bool(payload.get("preview_available")):
            working += 1
            results.append({
                "id": book.id,
                "title": book.title,
                "status": "working",
                "volume_id": volume_id,
            })
        else:
            restricted += 1
            results.append({
                "id": book.id,
                "title": book.title,
                "status": "restricted",
                "volume_id": volume_id,
            })

    return {
        "category": normalized_category,
        "total_checked": len(results),
        "working": working,
        "missing_identifier": missing_identifier,
        "restricted": restricted,
        "not_found": not_found,
        "errors": errors,
        "results": results,
    }


@router.post("/revalidate-links")
async def revalidate_book_links(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    result = await revalidate_links(db, limit=limit)
    return result


@router.get("", response_model=HybridBookListResponse)
def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    author: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = crud.list_hybrid_books(db, skip=skip, limit=limit, category=category, author=author, source=source)
    return HybridBookListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/stats")
def hybrid_stats(db: Session = Depends(get_db)):
    all_books = db.query(HybridBook)
    total_books = all_books.count()
    total_verified = all_books.filter(HybridBook.is_verified == True).count()
    total_sources = all_books.with_entities(HybridBook.source).distinct().count()
    return {
        "total_books": total_books,
        "total_verified": total_verified,
        "total_sources": total_sources,
    }


@router.get("/categories")
def hybrid_categories(db: Session = Depends(get_db)):
    grouped = (
        db.query(HybridBook.category, func.count(HybridBook.id))
        .filter(HybridBook.category.isnot(None))
        .group_by(HybridBook.category)
        .all()
    )

    counts_by_slug = {
        (name or "").strip().lower().replace(" ", "-"): int(count)
        for name, count in grouped
        if name
    }

    defaults = [
        {
            **meta,
            "book_count": counts_by_slug.get(meta["slug"], 0),
        }
        for meta in DEFAULT_CATEGORY_META
    ]

    extra_categories = [
        {
            "name": name,
            "slug": slug,
            "description": "",
            "book_count": count,
        }
        for slug, count in counts_by_slug.items()
        if slug and slug not in {meta["slug"] for meta in DEFAULT_CATEGORY_META}
        for name, _ in grouped
        if (name or "").strip().lower().replace(" ", "-") == slug
    ]

    return defaults + extra_categories


@router.get("/search", response_model=HybridBookListResponse)
def search_books(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = crud.search_hybrid_books(db, q=q, skip=skip, limit=limit, category=category)
    return HybridBookListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=HybridBookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(HybridBook).filter(HybridBook.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    book = db.query(HybridBook).filter(HybridBook.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.local_file_path and os.path.exists(book.local_file_path):
        os.remove(book.local_file_path)

    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}


@router.get("/{book_id}/view")
def view_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(HybridBook).filter(HybridBook.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.local_file_path:
        if not os.path.exists(book.local_file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        return FileResponse(
            path=book.local_file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{book.title}.pdf"'},
        )

    if _is_google_books_source(book):
        embed_url = _google_embed_url_from_book(book)
        target = embed_url or book.preview_link or book.download_link
        if target:
            return RedirectResponse(url=target, status_code=307)

    target = book.download_link or book.preview_link
    if not target:
        raise HTTPException(status_code=404, detail="No viewable resource available")

    return RedirectResponse(url=target, status_code=307)


@router.get("/{book_id}/download")
def download_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(HybridBook).filter(HybridBook.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.local_file_path:
        if not os.path.exists(book.local_file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        return FileResponse(
            path=book.local_file_path,
            media_type="application/pdf",
            filename=f"{book.title}.pdf",
        )

    return RedirectResponse(url=book.download_link, status_code=307)


@router.get("/{book_id}/stream")
async def stream_book_pdf(book_id: int, db: Session = Depends(get_db)):
    book = db.query(HybridBook).filter(HybridBook.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.local_file_path:
        if not os.path.exists(book.local_file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        return FileResponse(path=book.local_file_path, media_type="application/pdf")

    if _is_google_books_source(book):
        embed_url = _google_embed_url_from_book(book)
        target = embed_url or book.preview_link or book.download_link
        if target:
            return RedirectResponse(url=target, status_code=307)
        raise HTTPException(status_code=404, detail="No embeddable Google Books preview is available for this book")

    if not book.download_link:
        raise HTTPException(status_code=404, detail="No PDF link available")

    client = httpx.AsyncClient(timeout=httpx.Timeout(timeout=60.0, connect=15.0), follow_redirects=True)
    try:
        upstream = await client.send(
            client.build_request(
                "GET",
                book.download_link,
                headers={
                    "Accept": "application/pdf,*/*;q=0.8",
                    "User-Agent": "Academic-E-Library/1.0",
                },
            ),
            stream=True,
        )
    except httpx.HTTPError as exc:
        await client.aclose()
        fallback = book.preview_link or book.download_link
        if fallback:
            return RedirectResponse(url=fallback, status_code=307)
        raise HTTPException(status_code=502, detail=f"Unable to stream remote PDF: {exc}") from exc

    if upstream.status_code >= 400:
        await upstream.aclose()
        await client.aclose()
        fallback = book.preview_link or book.download_link
        if fallback:
            return RedirectResponse(url=fallback, status_code=307)
        raise HTTPException(status_code=upstream.status_code, detail="Remote PDF source returned an error")

    content_type = (upstream.headers.get("content-type") or "").lower()
    content_disposition = (upstream.headers.get("content-disposition") or "").lower()
    final_url = str(upstream.url).lower()

    looks_like_pdf_by_headers = (
        "pdf" in content_type
        or "application/octet-stream" in content_type
        or ".pdf" in content_disposition
        or ".pdf" in final_url
    )

    stream_iter = upstream.aiter_bytes()
    first_chunk = b""

    if not looks_like_pdf_by_headers:
        try:
            first_chunk = await anext(stream_iter)
        except StopAsyncIteration:
            first_chunk = b""

        if not first_chunk.startswith(b"%PDF-"):
            await upstream.aclose()
            await client.aclose()
            fallback = book.preview_link or book.download_link
            if fallback:
                return RedirectResponse(url=fallback, status_code=307)
            raise HTTPException(status_code=422, detail="No embeddable PDF is available for this book")

    headers = {}
    for h in ("content-length", "accept-ranges", "cache-control", "etag", "last-modified"):
        if upstream.headers.get(h):
            headers[h] = upstream.headers[h]

    async def _cleanup():
        await upstream.aclose()
        await client.aclose()

    async def _iter_pdf_bytes():
        if first_chunk:
            yield first_chunk
        async for chunk in stream_iter:
            yield chunk

    return StreamingResponse(
        _iter_pdf_bytes(),
        media_type=upstream.headers.get("content-type") or "application/pdf",
        headers=headers,
        background=BackgroundTask(_cleanup),
    )


@router.post("/upload", response_model=UploadBookResponse)
async def upload_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    publisher: str = Form(""),
    published_year: str = Form(""),
    cover_image: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are allowed")

    normalized_category = normalize_category(category)
    if not normalized_category:
        raise HTTPException(status_code=400, detail="Category must be one of: cybersecurity, data-science, artificial-intelligence")

    file_path, file_size = await save_uploaded_pdf(file)
    book = crud.create_hybrid_book(
        db,
        title=title,
        author=author,
        description=description or "No description provided.",
        category=normalized_category,
        cover_image=cover_image,
        preview_link="",
        download_link="",
        source="Manual Upload",
        is_verified=True,
        file_size=file_size,
        publisher=publisher,
        published_year=published_year,
        local_file_path=file_path,
        created_at=datetime.now(timezone.utc),
        last_checked=datetime.now(timezone.utc),
    )

    return UploadBookResponse(id=book.id, message="PDF uploaded and stored successfully")
