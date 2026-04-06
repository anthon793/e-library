from pydantic import BaseModel
from typing import Optional


class BookCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = ""
    category_id: Optional[int] = None
    cover_image: Optional[str] = ""
    book_type: str  # external / drive / upload / archive
    preview_link: Optional[str] = ""
    view_link: Optional[str] = ""
    download_link: Optional[str] = ""
    source: Optional[str] = ""
    api_id: Optional[str] = ""
    archive_id: Optional[str] = ""


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    cover_image: Optional[str] = None
    preview_link: Optional[str] = None
    view_link: Optional[str] = None
    download_link: Optional[str] = None
    archive_id: Optional[str] = None


class DriveBookCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = ""
    category_id: Optional[int] = None
    cover_image: Optional[str] = ""
    drive_link: str


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    description: str
    category_id: Optional[int]
    cover_image: str
    book_type: str
    preview_link: str
    view_link: str
    download_link: str
    file_path: str
    source: str
    api_id: str
    archive_id: str
    download_count: int
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class ExternalBookResult(BaseModel):
    api_id: str
    title: str
    author: str
    description: str
    cover_image: str
    view_link: str
    source: str = "open_library"
