from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserShort


class TeamCreate(BaseModel):
    name: str
    description: str
    hackathon_id: int


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TeamMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    joined_at: datetime
    user: UserShort


class TeamJoinRequest(BaseModel):
    role: str = "member"


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    hackathon_id: int
    created_at: datetime


class TeamDetail(TeamResponse):
    created_by: UserShort
    memberships: list[TeamMembershipResponse]
