from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.review import ReviewResponse
from app.schemas.team import TeamResponse
from app.schemas.task import TaskResponse
from app.schemas.user import UserShort


class SubmissionCreate(BaseModel):
    task_id: int
    team_id: int
    repository_url: str
    description: str
    status: str = "submitted"


class SubmissionUpdate(BaseModel):
    repository_url: str | None = None
    description: str | None = None
    status: str | None = None


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_url: str
    description: str
    status: str
    submitted_at: datetime


class SubmissionDetail(SubmissionResponse):
    task: TaskResponse
    team: TeamResponse
    submitted_by: UserShort
    reviews: list[ReviewResponse]
