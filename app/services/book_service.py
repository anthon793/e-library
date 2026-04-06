import os
import shutil
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import UploadFile

from app.config import settings
from app.models.book import Book, BookType
from app.models.download import Download
from app.models.category import Category


def _allowed_books_query(db: Session):
    return db.query(Book)


def get_books(db: Session, skip: int = 0, limit: int = 20, category_id: int = None):
    query = _allowed_books_query(db)
    if category_id:
        query = query.filter(Book.category_id == category_id)
    return query.order_by(Book.created_at.desc()).offset(skip).limit(limit).all()


def get_book_by_id(db: Session, book_id: int):
    return _allowed_books_query(db).filter(Book.id == book_id).first()


def get_allowed_category(db: Session, category_id: int):
    if category_id is None:
        return None
    return db.query(Category).filter(Category.id == category_id).first()


def search_books(db: Session, q: str, category_id: int = None):
    query = _allowed_books_query(db).filter(
        or_(
            Book.title.ilike(f"%{q}%"),
            Book.author.ilike(f"%{q}%"),
            Book.description.ilike(f"%{q}%"),
        )
    )
    if category_id:
        query = query.filter(Book.category_id == category_id)
    return query.order_by(Book.created_at.desc()).all()


def create_book(db: Session, **kwargs) -> Book:
    book = Book(**kwargs)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, **kwargs) -> Book | None:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> bool:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return False
    # Delete physical file if uploaded
    if book.file_path and os.path.exists(book.file_path):
        os.remove(book.file_path)
    db.query(Download).filter(Download.book_id == book_id).delete(synchronize_session=False)
    db.delete(book)
    db.commit()
    return True


async def save_uploaded_file(file: UploadFile) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # Create unique filename
    import uuid
    ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return filepath


def record_download(db: Session, book_id: int, user_id: int = None):
    download = Download(book_id=book_id, user_id=user_id)
    db.add(download)
    # Increment download count on book
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.download_count = (book.download_count or 0) + 1
    db.commit()


def get_book_count(db: Session, category_id: int = None) -> int:
    query = _allowed_books_query(db)
    if category_id:
        query = query.filter(Book.category_id == category_id)
    return query.count()


def get_recent_books(db: Session, limit: int = 8):
    return _allowed_books_query(db).order_by(Book.created_at.desc()).limit(limit).all()


def get_popular_books(db: Session, limit: int = 8):
    return _allowed_books_query(db).order_by(Book.download_count.desc()).limit(limit).all()


def get_download_stats(db: Session):
    return db.query(Download).count()


def get_allowed_book_count(db: Session) -> int:
    return _allowed_books_query(db).count()
