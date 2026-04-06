from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class HybridBook(Base):
    __tablename__ = "hybrid_books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(300), nullable=False, index=True)
    author = Column(String(300), nullable=False, index=True)
    description = Column(Text, default="")
    category = Column(String(120), default="", index=True)
    cover_image = Column(String(700), default="")
    preview_link = Column(String(1000), default="")
    download_link = Column(String(1000), nullable=False)
    source = Column(String(80), nullable=False, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    file_size = Column(Integer, default=0)

    publisher = Column(String(300), default="")
    published_year = Column(String(20), default="")
    local_file_path = Column(String(700), default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
