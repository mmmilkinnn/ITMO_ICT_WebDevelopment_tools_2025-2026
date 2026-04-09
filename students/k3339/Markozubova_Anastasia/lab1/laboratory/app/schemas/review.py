from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserShort


class ReviewCreate(BaseModel):
    submission_id: int
    score: int = Field(ge=1, le=100)
    comment: str


class ReviewUpdate(BaseModel):
    score: int | None = Field(default=None, ge=1, le=100)
    comment: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score: int
    comment: str
    created_at: datetime
    reviewer: UserShort
