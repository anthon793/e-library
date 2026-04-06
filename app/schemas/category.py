from pydantic import BaseModel
from typing import Optional


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    icon: str
    book_count: Optional[int] = 0

    class Config:
        from_attributes = True
