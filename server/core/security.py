import os
from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import jwt, JWTError
import bcrypt

# Secret key and algorithm configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ai-short-drama-dev-secret-key-change-in-prod-2026")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # Default 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password safely using native bcrypt."""
    try:
        if not plain_password or not hashed_password:
            return False
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for password safely using native bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate JWT access token.
    data usually contains 'sub' (username) and 'role'.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    Returns the payload dictionary or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
