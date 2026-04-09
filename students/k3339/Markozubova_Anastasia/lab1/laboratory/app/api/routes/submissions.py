from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.models.review import Review
from app.models.submission import Submission
from app.models.task import Task
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionResponse,
    SubmissionUpdate,
)

router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.get(Task, payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    team = db.get(Team, payload.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.hackathon_id != task.hackathon_id:
        raise HTTPException(
            status_code=400,
            detail="Team and task must belong to the same hackathon"
        )

    membership = db.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == payload.team_id,
            TeamMembership.user_id == current_user.id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You can submit only for your own team"
        )

    new_submission = Submission(
        task_id=payload.task_id,
        team_id=payload.team_id,
        submitted_by_id=current_user.id,
        repository_url=payload.repository_url,
        description=payload.description,
        status=payload.status,
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return new_submission



@router.get("/", response_model=list[SubmissionResponse])
def get_all_submissions(db: Session = Depends(get_db)):
    submissions = db.scalars(select(Submission)).all()
    return list(submissions)


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission_by_id(submission_id: int, db: Session = Depends(get_db)):
    query = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.task),
            selectinload(Submission.team),
            selectinload(Submission.submitted_by),
            selectinload(Submission.reviews).selectinload(Review.reviewer),
        )
    )

    submission = db.scalar(query)

    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    return submission


@router.patch("/{submission_id}", response_model=SubmissionResponse)
def update_submission(
    submission_id: int,
    payload: SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.get(Submission, submission_id)

    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.submitted_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can edit the submission")

    if payload.repository_url is not None:
        submission.repository_url = payload.repository_url

    if payload.description is not None:
        submission.description = payload.description

    if payload.status is not None:
        submission.status = payload.status

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return submission


@router.delete("/{submission_id}")
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.get(Submission, submission_id)

    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.submitted_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can delete the submission")

    db.delete(submission)
    db.commit()

    return {"message": "Submission deleted successfully"}
