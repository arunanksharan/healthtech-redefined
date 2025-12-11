"""
JWT token generation and validation
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from loguru import logger

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-please")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    additional_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        email: User email
        additional_claims: Additional claims to include in token
        expires_delta: Optional custom expiration time

    Returns:
        str: JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID
) -> str:
    """
    Create a JWT refresh token

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID

    Returns:
        str: JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        Dict with token payload if valid, None if invalid

    Raises:
        JWTError: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
            return None

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None

        return payload

    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        return None


def decode_token_no_verify(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode token without verification (for debugging)

    Args:
        token: JWT token string

    Returns:
        Dict with token payload or None
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


def get_token_exp_time(token: str) -> Optional[datetime]:
    """
    Get expiration time from token

    Args:
        token: JWT token string

    Returns:
        datetime of expiration or None
    """
    payload = decode_token_no_verify(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired

    Args:
        token: JWT token string

    Returns:
        bool: True if expired, False if valid
    """
    exp_time = get_token_exp_time(token)
    if exp_time:
        return exp_time < datetime.utcnow()
    return True
