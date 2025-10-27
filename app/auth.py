"""Authentication utilities for JWT token management."""
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Cookie, HTTPException, status

from app.config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS, DEFAULT_USERS


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify user credentials.

    Args:
        username: Username to verify
        password: Password to verify

    Returns:
        True if credentials are valid, False otherwise
    """
    return username in DEFAULT_USERS and DEFAULT_USERS[username] == password


def create_access_token(username: str) -> str:
    """
    Create a JWT access token.

    Args:
        username: Username to encode in the token

    Returns:
        Encoded JWT token string
    """
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": username,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Username from token if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(access_token: str = Cookie(None)) -> str:
    """
    Get current user from JWT token in cookie.

    Args:
        access_token: JWT token from cookie

    Returns:
        Username if token is valid

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - missing token"
        )

    username = verify_token(access_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return username
