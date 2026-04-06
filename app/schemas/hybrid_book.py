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
    description: str
    category: str
    cover_image: str
    preview_link: str
    download_link: str
    source: str
    is_verified: bool
    file_size: int
    publisher: str
    published_year: str
    created_at: datetime
    last_checked: datetime


class HybridBookResponse(HybridBookBase):
    id: int

    class Config:
        orm_mode = True


class HybridBookListResponse(BaseModel):
    items: list[HybridBookResponse]
    total: int
    skip: int
    limit: int


class UploadBookResponse(BaseModel):
    id: int
    message: str
