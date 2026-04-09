from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.models.hackathon import Hackathon
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.team import TeamCreate, TeamDetail, TeamJoinRequest, TeamResponse, TeamUpdate

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.post("/", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hackathon = db.get(Hackathon, payload.hackathon_id)

    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    new_team = Team(
        name=payload.name,
        description=payload.description,
        hackathon_id=payload.hackathon_id,
        created_by_id=current_user.id,
    )

    db.add(new_team)
    db.flush()

    captain_membership = TeamMembership(
        team_id=new_team.id,
        user_id=current_user.id,
        role="captain",
    )

    db.add(captain_membership)
    db.commit()

    query = (
        select(Team)
        .where(Team.id == new_team.id)
        .options(
            selectinload(Team.created_by),
            selectinload(Team.memberships).selectinload(TeamMembership.user),
        )
    )

    team = db.scalar(query)
    return team


@router.get("/", response_model=list[TeamResponse])
def get_all_teams(db: Session = Depends(get_db)):
    teams = db.scalars(select(Team)).all()
    return list(teams)


@router.get("/{team_id}", response_model=TeamDetail)
def get_team_by_id(team_id: int, db: Session = Depends(get_db)):
    query = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.created_by),
            selectinload(Team.memberships).selectinload(TeamMembership.user),
        )
    )

    team = db.scalar(query)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return team


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.get(Team, team_id)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team creator can edit the team")

    if payload.name is not None:
        team.name = payload.name

    if payload.description is not None:
        team.description = payload.description

    db.add(team)
    db.commit()
    db.refresh(team)

    return team


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.get(Team, team_id)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team creator can delete the team")

    db.delete(team)
    db.commit()

    return {"message": "Team deleted successfully"}


@router.post("/{team_id}/join", response_model=TeamDetail)
def join_team(
    team_id: int,
    payload: TeamJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.get(Team, team_id)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    existing_membership = db.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
        )
    )

    if existing_membership is not None:
        raise HTTPException(status_code=400, detail="You are already a member of this team")

    new_membership = TeamMembership(
        team_id=team_id,
        user_id=current_user.id,
        role=payload.role,
    )

    db.add(new_membership)
    db.commit()

    query = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.created_by),
            selectinload(Team.memberships).selectinload(TeamMembership.user),
        )
    )

    updated_team = db.scalar(query)
    return updated_team
