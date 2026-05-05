from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    """Schema for creating or updating a rating."""
    score: int = Field(..., ge=1, le=5)
    user_identifier: str = Field(..., min_length=36, max_length=255)
    comment: Optional[str] = Field(None, max_length=1000)


class RatingResponse(BaseModel):
    """Schema for rating response."""
    id: int
    course_id: int
    user_identifier: str
    score: int
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime


class RatingStats(BaseModel):
    """Schema for rating statistics."""
    average_rating: float
    ratings_count: int
