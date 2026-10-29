from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from models.database import get_session, User, UserRole
from core.security import decode_access_token

# HTTPBearer allows passing Authorization: Bearer <token>
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Authenticate request via JWT Bearer token and return the active User.
    Raises 401 if missing or invalid token, 403 if user is disabled.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing username subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
        
    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Returns the current User if valid token is provided, else returns None.
    Does not raise 401.
    """
    if not credentials or not credentials.credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    username: Optional[str] = payload.get("sub")
    if not username:
        return None
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        return None
    return user


def require_role(*required_roles: str):
    """
    Dependency factory to check if current user has one of the allowed roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{current_user.role}'"
            )
        return current_user
    return role_checker


# Convenient role dependencies
get_current_admin = require_role(UserRole.ADMIN.value)
get_current_operator = require_role(UserRole.ADMIN.value, UserRole.OPERATOR.value)
