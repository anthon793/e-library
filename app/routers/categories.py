from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import ALLOWED_CATEGORY_SLUGS
from app.dependencies import get_db
from app.models.category import Category
from app.models.book import Book, BookType

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("")
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.slug.in_(ALLOWED_CATEGORY_SLUGS)).order_by(Category.name).all()
    results = []
    for cat in categories:
        count = (
            db.query(Book)
            .join(Category)
            .filter(
                Book.category_id == cat.id,
                Category.slug.in_(ALLOWED_CATEGORY_SLUGS),
                Book.book_type == BookType.archive,
                Book.source == "Internet Archive",
            )
            .count()
        )
        results.append({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "icon": cat.icon,
            "book_count": count,
        })
    return results
