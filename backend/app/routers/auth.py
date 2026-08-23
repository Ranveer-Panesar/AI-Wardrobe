from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.schemas.user import LoginRequest, RefreshRequest, SignupRequest, TokenResponse, UserResponse
from app.services.auth_service import create_user, get_user_by_email, get_user_by_id, get_user_by_phone

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if get_user_by_phone(db, payload.phone):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

    user = create_user(
        db,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    return UserResponse(id=str(user.id), email=user.email, phone=user.phone)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        # Deliberately the same error for "no such user" and "wrong password" —
        # don't leak which one it was, that's a user-enumeration vector.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Issues a new pair (rotates the refresh token too) rather than just a
    # new access token — means a leaked-and-reused old refresh token stops
    # working the moment the legitimate client refreshes.
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
