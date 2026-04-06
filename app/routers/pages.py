from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db, get_current_user_optional
from app.services import book_service
from app.models.category import Category
from app.models.book import Book
from app.models.user import User

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")


def get_categories(db: Session):
    return db.query(Category).order_by(Category.name).all()


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    recent_books = book_service.get_recent_books(db, limit=8)
    popular_books = book_service.get_popular_books(db, limit=8)
    categories = get_categories(db)
    total_books = book_service.get_book_count(db)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "recent_books": recent_books,
        "popular_books": popular_books,
        "categories": categories,
        "total_books": total_books,
    })


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/library", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/library", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "user": None})


@router.get("/library", response_class=HTMLResponse)
def library_page(
    request: Request,
    category: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    user = get_current_user_optional(request, db)
    categories = get_categories(db)

    category_id = None
    active_category = None
    if category:
        cat = db.query(Category).filter(Category.slug == category).first()
        if cat:
            category_id = cat.id
            active_category = cat

    skip = (page - 1) * 20
    books = book_service.get_books(db, skip=skip, limit=20, category_id=category_id)
    total = book_service.get_book_count(db, category_id=category_id)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "books": books,
        "categories": categories,
        "active_category": active_category,
        "page": page,
        "total": total,
        "has_next": skip + 20 < total,
    })


@router.get("/library/book/{book_id}", response_class=HTMLResponse)
def book_detail_page(request: Request, book_id: int, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        return RedirectResponse(url="/library", status_code=302)

    # Get related books from same category
    related = []
    if book.category_id:
        related = db.query(Book).filter(
            Book.category_id == book.category_id,
            Book.id != book.id,
        ).limit(4).all()

    categories = get_categories(db)

    return templates.TemplateResponse("book_detail.html", {
        "request": request,
        "user": user,
        "book": book,
        "related_books": related,
        "categories": categories,
    })


@router.get("/library/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = Query(""),
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user_optional(request, db)
    categories = get_categories(db)
    books = []
    if q:
        books = book_service.search_books(db, q=q, category_id=category_id)

    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "user": user,
        "books": books,
        "query": q,
        "categories": categories,
        "category_id": category_id,
    })


@router.get("/library/upload", response_class=HTMLResponse)
def upload_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role.value not in ("lecturer", "admin"):
        return RedirectResponse(url="/login", status_code=302)
    categories = get_categories(db)
    return templates.TemplateResponse("upload_book.html", {
        "request": request,
        "user": user,
        "categories": categories,
    })


@router.get("/library/import", response_class=HTMLResponse)
def import_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role.value not in ("lecturer", "admin"):
        return RedirectResponse(url="/login", status_code=302)
    categories = get_categories(db)
    return templates.TemplateResponse("add_external.html", {
        "request": request,
        "user": user,
        "categories": categories,
    })


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role.value != "admin":
        return RedirectResponse(url="/login", status_code=302)

    total_books = book_service.get_book_count(db)
    total_downloads = book_service.get_download_stats(db)
    total_users = db.query(User).count()
    recent_books = book_service.get_recent_books(db, limit=10)
    categories = get_categories(db)

    # Category stats
    cat_stats = []
    for cat in categories:
        count = db.query(Book).filter(Book.category_id == cat.id).count()
        cat_stats.append({"name": cat.name, "icon": cat.icon, "count": count})

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": user,
        "total_books": total_books,
        "total_downloads": total_downloads,
        "total_users": total_users,
        "recent_books": recent_books,
        "categories": categories,
        "cat_stats": cat_stats,
    })


@router.get("/admin/books", response_class=HTMLResponse)
def admin_manage_books(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role.value != "admin":
        return RedirectResponse(url="/login", status_code=302)

    books = book_service.get_books(db, limit=200)
    categories = get_categories(db)

    return templates.TemplateResponse("admin/manage_books.html", {
        "request": request,
        "user": user,
        "books": books,
        "categories": categories,
    })


@router.get("/admin/users", response_class=HTMLResponse)
def admin_manage_users(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role.value != "admin":
        return RedirectResponse(url="/login", status_code=302)

    users = db.query(User).order_by(User.created_at.desc()).all()
    categories = get_categories(db)

    return templates.TemplateResponse("admin/manage_users.html", {
        "request": request,
        "user": user,
        "users": users,
        "categories": categories,
    })
