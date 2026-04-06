import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

from app.database import engine, Base, SessionLocal, create_tables
from app.config import settings
from app.models import User, Category, Book, Download, GoogleBook
from app.models.user import UserRole
from app.services.auth_service import hash_password

# Create FastAPI app
app = FastAPI(
    title="Academic E-Library",
    description="Digital Academic E-Library Aggregation and Repository System",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving uploaded files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
from app.routers import auth, books, categories, external_api, archive, pdf_proxy, book_gateway, hybrid_books, google_books

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)
app.include_router(external_api.router)
app.include_router(archive.router)
app.include_router(pdf_proxy.router)
app.include_router(book_gateway.router)
app.include_router(hybrid_books.router)
app.include_router(google_books.router)


def _ensure_archive_columns(db: Session):
    inspector = inspect(db.bind)
    columns = {col["name"] for col in inspector.get_columns("books")}

    if "preview_link" not in columns:
        db.execute(text("ALTER TABLE books ADD COLUMN preview_link VARCHAR(500) DEFAULT ''"))
    if "archive_id" not in columns:
        db.execute(text("ALTER TABLE books ADD COLUMN archive_id VARCHAR(120) DEFAULT ''"))
    db.commit()


def _ensure_hybrid_columns(db: Session):
    inspector = inspect(db.bind)
    columns = {col["name"] for col in inspector.get_columns("hybrid_books")}

    if "preview_link" not in columns:
        db.execute(text("ALTER TABLE hybrid_books ADD COLUMN preview_link VARCHAR(1000) DEFAULT ''"))
    db.commit()


# Default categories to seed
DEFAULT_CATEGORIES = [
    {"name": "Cybersecurity", "slug": "cybersecurity", "description": "Information security, ethical hacking, and network defense", "icon": "🔒"},
    {"name": "Data Science", "slug": "data-science", "description": "Data analysis, statistics, and machine learning", "icon": "📊"},
    {"name": "Artificial Intelligence", "slug": "artificial-intelligence", "description": "AI, deep learning, and neural networks", "icon": "🤖"},
]


@app.on_event("startup")
async def startup_event():
    """Create tables, seed categories, users, and books."""
    create_tables()

    db = SessionLocal()
    try:
        _ensure_archive_columns(db)
        _ensure_hybrid_columns(db)

        # Seed categories
        for cat_data in DEFAULT_CATEGORIES:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                cat = Category(**cat_data)
                db.add(cat)

        # Seed default admin user
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@elibrary.edu",
                full_name="System Administrator",
                hashed_password=hash_password("admin123"),
                role=UserRole.admin,
            )
            db.add(admin)

        # Seed a demo lecturer
        lecturer = db.query(User).filter(User.username == "lecturer").first()
        if not lecturer:
            lecturer = User(
                username="lecturer",
                email="lecturer@elibrary.edu",
                full_name="Dr. Demo Lecturer",
                hashed_password=hash_password("lecturer123"),
                role=UserRole.lecturer,
            )
            db.add(lecturer)

        db.commit()

        # Book seeding intentionally disabled while migrating fetch strategy.

    finally:
        db.close()


# Serve React build if it exists (production)
react_build_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(react_build_path):
    app.mount("/", StaticFiles(directory=react_build_path, html=True), name="react")
