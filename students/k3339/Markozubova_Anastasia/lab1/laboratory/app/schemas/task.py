from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    hackathon_id: int
    title: str
    description: str
    requirements: str
    evaluation_criteria: str
    is_active: bool = True


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    requirements: str | None = None
    evaluation_criteria: str | None = None
    is_active: bool | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hackathon_id: int
    title: str
    description: str
    requirements: str
    evaluation_criteria: str
    is_active: bool
    created_at: datetime
