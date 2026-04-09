from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.hackathon import Hackathon
from app.models.task import Task
from app.api.deps import get_current_organizer, get_current_user, get_db
from app.models.review import Review
from app.models.submission import Submission
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    submission = db.get(Submission, payload.submission_id)

    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    task = db.get(Task, submission.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    hackathon = db.get(Hackathon, task.hackathon_id)
    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can review submissions only in your own hackathon"
        )

    new_review = Review(
        submission_id=payload.submission_id,
        reviewer_id=current_user.id,
        score=payload.score,
        comment=payload.comment,
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review



@router.get("/", response_model=list[ReviewResponse])
def get_all_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Review).options(selectinload(Review.reviewer))
    reviews = db.scalars(query).all()
    return list(reviews)


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review_by_id(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Review)
        .where(Review.id == review_id)
        .options(selectinload(Review.reviewer))
    )

    review = db.scalar(query)

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.patch("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    review = db.get(Review, review_id)

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.reviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can edit the review")

    if payload.score is not None:
        review.score = payload.score

    if payload.comment is not None:
        review.comment = payload.comment

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    review = db.get(Review, review_id)

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.reviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can delete the review")

    db.delete(review)
    db.commit()

    return {"message": "Review deleted successfully"}
