from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AutoImportRequest(BaseModel):
    query: str = Field(min_length=2)
    category: Optional[str] = ""
    field: str = Field(default="all")
    max_results_per_source: int = Field(default=8, ge=1, le=30)


class AutoImportResponse(BaseModel):
    job_id: str
    status: str
    message: str


class ImportJobStatus(BaseModel):
    job_id: str
    status: str
    query: str
    imported_count: int
    checked_count: int
    errors: list[str]


class HybridBookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = ""
    category: Optional[str] = ""
    cover_image: Optional[str] = ""
    preview_link: Optional[str] = ""
    download_link: Optional[str] = ""
    source: Optional[str] = ""
    is_verified: bool = False
    file_size: int = 0
    publisher: Optional[str] = ""
    published_year: Optional[str] = ""
    created_at: Optional[datetime] = None
    last_checked: Optional[datetime] = None


class HybridBookResponse(HybridBookBase):
    id: int

    class Config:
        from_attributes = True


class HybridBookListResponse(BaseModel):
    items: list[HybridBookResponse]
    total: int
    skip: int
    limit: int


class UploadBookResponse(BaseModel):
    id: int
    message: str
