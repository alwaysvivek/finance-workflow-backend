from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import Any
from datetime import timedelta

from app.db.session import get_session
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.models import User
from app.schemas.schemas import Token, UserCreate, UserResponse, StandardResponse
from app.api.deps import get_current_active_user

router = APIRouter()

@router.post("/auth/register", response_model=StandardResponse[UserResponse])
def register_user(
    *,
    db: Session = Depends(get_session),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user.
    """
    user = db.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
        
    user_obj = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        company_id=user_in.company_id,
        is_active=True
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return {"data": user_obj, "meta": {}}

@router.post("/auth/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/users/me", response_model=StandardResponse[UserResponse])
def read_users_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return {"data": current_user, "meta": {}}
