from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_db
from app.models.hackathon import Hackathon
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    hackathon = db.get(Hackathon, payload.hackathon_id)

    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can create tasks only for your own hackathon"
        )

    new_task = Task(
        hackathon_id=payload.hackathon_id,
        title=payload.title,
        description=payload.description,
        requirements=payload.requirements,
        evaluation_criteria=payload.evaluation_criteria,
        is_active=payload.is_active,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task



@router.get("/", response_model=list[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.scalars(select(Task)).all()
    return list(tasks)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    hackathon = db.get(Hackathon, task.hackathon_id)
    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can edit only tasks from your own hackathon"
        )

    if payload.title is not None:
        task.title = payload.title

    if payload.description is not None:
        task.description = payload.description

    if payload.requirements is not None:
        task.requirements = payload.requirements

    if payload.evaluation_criteria is not None:
        task.evaluation_criteria = payload.evaluation_criteria

    if payload.is_active is not None:
        task.is_active = payload.is_active

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_organizer),
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    hackathon = db.get(Hackathon, task.hackathon_id)
    if hackathon is None:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if hackathon.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can delete only tasks from your own hackathon"
        )

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

