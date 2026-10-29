from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from models.database import get_session, User, UserRole, UserCreate, UserRead, Token
from core.security import verify_password, get_password_hash, create_access_token
from api.deps import get_current_user, get_current_admin
from middleware.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead)
@limiter.limit("10/minute")
def register(
    request: Request,
    user_in: UserCreate,
    session: Session = Depends(get_session)
):
    """
    Register a new user.
    The very first registered user is automatically given the ADMIN role.
    Subsequent users default to OPERATOR unless explicitly set and allowed.
    """
    existing_user = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if this is the first user in system
    first_user = session.exec(select(User)).first() is None
    role = UserRole.ADMIN.value if first_user else (user_in.role or UserRole.OPERATOR.value)

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(
    request: Request,
    user_in: UserCreate,
    session: Session = Depends(get_session)
):
    """
    Authenticate user with username and password, return JWT Bearer token.
    Rate limited to 10 attempts per minute to prevent brute-force attacks.
    """
    user = session.exec(select(User).where(User.username == user_in.username)).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
        
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username
    )


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get profile information of the currently authenticated user.
    """
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Generate a fresh JWT token for an already authenticated active user.
    """
    new_token = create_access_token(data={"sub": current_user.username, "role": current_user.role})
    return Token(
        access_token=new_token,
        token_type="bearer",
        role=current_user.role,
        username=current_user.username
    )


@router.get("/users", response_model=List[UserRead])
def list_users(
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    """
    List all registered users. Restricted to ADMIN role only.
    """
    users = session.exec(select(User)).all()
    return users
