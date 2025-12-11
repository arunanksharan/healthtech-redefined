"""
JWT Token Handling
Provides JWT encoding, decoding, and validation
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

import jwt
from loguru import logger

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-use-env-var")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    scopes: list[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token

    Args:
        user_id: User UUID
        tenant_id: Organization/tenant UUID
        email: User email
        scopes: List of permission scopes
        expires_delta: Optional custom expiration

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "scopes": scopes,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token

    Args:
        user_id: User UUID
        tenant_id: Organization/tenant UUID
        expires_delta: Optional custom expiration

    Returns:
        JWT refresh token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """
    Decode JWT token without verification

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        jwt.DecodeError: If token is malformed
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
            return None

        # Check expiration (jwt.decode already does this, but let's be explicit)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def get_token_exp(token: str) -> Optional[datetime]:
    """
    Get token expiration time

    Args:
        token: JWT token string

    Returns:
        Expiration datetime or None if invalid
    """
    try:
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp)
        return None
    except Exception:
        return None
