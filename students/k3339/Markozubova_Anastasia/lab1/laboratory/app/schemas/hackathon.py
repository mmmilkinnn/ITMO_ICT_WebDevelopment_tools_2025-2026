from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserShort


class HackathonCreate(BaseModel):
    title: str
    description: str
    start_date: date
    end_date: date
    status: str = "draft"


class HackathonUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class RegistrationUpdate(BaseModel):
    status: str


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    registered_at: datetime
    user: UserShort


class TeamShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str


class TaskShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    is_active: bool


class HackathonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    start_date: date
    end_date: date
    status: str
    organizer: UserShort


class HackathonDetail(HackathonResponse):
    registrations: list[RegistrationResponse]
    teams: list[TeamShort]
    tasks: list[TaskShort]
