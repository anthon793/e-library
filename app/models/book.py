import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class BookType(str, enum.Enum):
    external = "external"
    drive = "drive"
    upload = "upload"
    archive = "archive"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(300), nullable=False, index=True)
    author = Column(String(300), nullable=False, index=True)
    description = Column(Text, default="")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    cover_image = Column(String(500), default="")
    book_type = Column(Enum(BookType), nullable=False)
    preview_link = Column(String(500), default="")
    view_link = Column(String(500), default="")
    download_link = Column(String(500), default="")
    file_path = Column(String(500), default="")
    source = Column(String(50), default="")  # open_library / drive / upload
    api_id = Column(String(100), default="")
    archive_id = Column(String(120), default="")
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="books")
    downloads = relationship("Download", back_populates="book", cascade="all, delete-orphan")
