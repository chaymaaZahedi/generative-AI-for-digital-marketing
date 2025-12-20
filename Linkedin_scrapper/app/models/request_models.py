
from pydantic import BaseModel

from typing import Optional

from app.utils.locations import LocationEnum

class ScrapeRequest(BaseModel):
    keyword: str
    location: LocationEnum
    limit: int = 2

class AdvancedFilterRequest(BaseModel):
    keyword: Optional[str] = None
    location: Optional[LocationEnum] = None
    gender: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    education: Optional[str] = None
    limit: Optional[int] = None
