from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_organizer, get_current_user, get_db
from app.models.hackathon import Hackathon, HackathonRegistration
from app.models.user import User
from app.schemas.hackathon import (
    HackathonCreate,
    HackathonDetail,
    HackathonResponse,
    HackathonUpdate,
    RegistrationResponse,
    RegistrationUpdate,
)

router = APIRouter(prefix="/hackathons", tags=["Hackathons"])


@router.post("/", response_model=HackathonResponse, status_code=status.HTTP_201_CREATED)
def create_hackathon(
    payload: HackathonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    new_hackathon = Hackathon(
        title=payload.title,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
        organizer_id=current_user.id,
    )

    db.add(new_hackathon)
    db.commit()
    db.refresh(new_hackathon)

    return new_hackathon


@router.get("/", response_model=list[HackathonResponse])
def get_all_hackathons(db: Session = Depends(get_db)):
    query = select(Hackathon).options(selectinload(Hackathon.organizer))
    hackathons = db.scalars(query).all()
    return list(hackathons)


@router.get("/{hackathon_id}", response_model=HackathonDetail)
def get_hackathon_by_id(hackathon_id: int, db: Session = Depends(get_db)):
    query = (
        select(Hackathon)
        .where(Hackathon.id == hackathon_id)
        .options(
            selectinload(Hackathon.organizer),
            selectinload(Hackathon.registrations).selectinload(HackathonRegistration.user),
            selectinload(Hackathon.teams),
            selectinload(Hackathon.tasks),
        )
    )

    hackathon = db.scalar(query)

    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    return hackathon


@router.patch("/{hackathon_id}", response_model=HackathonResponse)
def update_hackathon(
    hackathon_id: int,
    payload: HackathonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    hackathon = db.get(Hackathon, hackathon_id)

    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can edit only your hackathons")

    if payload.title is not None:
        hackathon.title = payload.title

    if payload.description is not None:
        hackathon.description = payload.description

    if payload.start_date is not None:
        hackathon.start_date = payload.start_date

    if payload.end_date is not None:
        hackathon.end_date = payload.end_date

    if payload.status is not None:
        hackathon.status = payload.status

    db.add(hackathon)
    db.commit()
    db.refresh(hackathon)

    return hackathon


@router.delete("/{hackathon_id}")
def delete_hackathon(
    hackathon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    hackathon = db.get(Hackathon, hackathon_id)

    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can delete only your hackathons")

    db.delete(hackathon)
    db.commit()

    return {"message": "Hackathon deleted successfully"}


@router.post("/{hackathon_id}/register", response_model=RegistrationResponse)
def register_for_hackathon(
    hackathon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hackathon = db.get(Hackathon, hackathon_id)

    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    existing_registration = db.scalar(
        select(HackathonRegistration).where(
            HackathonRegistration.user_id == current_user.id,
            HackathonRegistration.hackathon_id == hackathon_id,
        )
    )

    if existing_registration is not None:
        raise HTTPException(status_code=400, detail="You are already registered")

    registration = HackathonRegistration(
        user_id=current_user.id,
        hackathon_id=hackathon_id,
        status="pending",
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration


@router.get("/{hackathon_id}/registrations", response_model=list[RegistrationResponse])
def get_hackathon_registrations(
    hackathon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(HackathonRegistration)
        .where(HackathonRegistration.hackathon_id == hackathon_id)
        .options(selectinload(HackathonRegistration.user))
    )

    registrations = db.scalars(query).all()
    return list(registrations)


@router.patch("/registrations/{registration_id}", response_model=RegistrationResponse)
def update_registration_status(
    registration_id: int,
    payload: RegistrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    registration = db.get(HackathonRegistration, registration_id)

    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    hackathon = db.get(Hackathon, registration.hackathon_id)
    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can manage registrations only for your own hackathon"
        )

    registration.status = payload.status

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration

