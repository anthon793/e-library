from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class GoogleBook(Base):
    __tablename__ = "google_books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    volume_id = Column(String(120), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    authors = Column(Text, default="")
    description = Column(Text, default="")
    publisher = Column(String(300), default="")
    published_date = Column(String(50), default="")
    categories = Column(Text, default="")
    thumbnail = Column(String(1000), default="")
    preview_link = Column(String(1000), default="")
    viewer_link = Column(String(1000), default="")
    info_link = Column(String(1000), default="")
    canonical_link = Column(String(1000), default="")
    viewability = Column(String(60), default="")
    preview_available = Column(Boolean, default=False, index=True)
    language = Column(String(20), default="")
    page_count = Column(Integer, default=0)
    isbn_10 = Column(String(20), default="", index=True)
    isbn_13 = Column(String(20), default="", index=True)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
