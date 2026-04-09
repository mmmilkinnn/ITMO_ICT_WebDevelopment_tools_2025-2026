from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user_by_email = db.scalar(
        select(User).where(User.email == payload.email)
    )
    if existing_user_by_email is not None:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    existing_user_by_phone = db.scalar(
        select(User).where(User.phone_number == payload.phone_number)
    )
    if existing_user_by_phone is not None:
        raise HTTPException(
            status_code=400,
            detail="User with this phone number already exists"
        )

    salt, password_hash = hash_password(payload.password)

    new_user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone_number=payload.phone_number,
        password_hash=password_hash,
        password_salt=salt,
        is_organizer=payload.is_organizer,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    password_is_correct = verify_password(
        payload.password,
        user.password_salt,
        user.password_hash
    )

    if not password_is_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(str(user.id))

    return TokenResponse(access_token=token)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    old_password_is_correct = verify_password(
        payload.old_password,
        current_user.password_salt,
        current_user.password_hash
    )

    if not old_password_is_correct:
        raise HTTPException(
            status_code=400,
            detail="Old password is incorrect"
        )

    new_salt, new_password_hash = hash_password(payload.new_password)

    current_user.password_salt = new_salt
    current_user.password_hash = new_password_hash

    db.add(current_user)
    db.commit()

    return {"message": "Password changed successfully"}
