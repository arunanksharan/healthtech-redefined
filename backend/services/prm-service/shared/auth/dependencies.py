"""
FastAPI Security Dependencies
Provides authentication and authorization dependencies for route protection
"""
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from shared.database.connection import get_db
from shared.database.models import User
from .jwt import verify_token


# HTTP Bearer token scheme
security = HTTPBearer()


@dataclass
class Principal:
    """
    Principal represents the authenticated user/actor
    Contains user identity and authorization context
    """
    user_id: UUID
    tenant_id: UUID  # org_id
    email: str
    scopes: List[str]
    is_active: bool = True

    # Alias for compatibility with original PRM code
    @property
    def org_id(self) -> UUID:
        """Alias for tenant_id"""
        return self.tenant_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token
    token = credentials.credentials

    # Verify token
    payload = verify_token(token, token_type="access")
    if payload is None:
        raise credentials_exception

    # Extract user_id
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_principal(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Principal:
    """
    Get Principal (user identity and context) from JWT token

    This is a faster alternative to get_current_user when you don't need
    the full User object from the database.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        Principal object with user context

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token
    token = credentials.credentials

    # Verify token
    payload = verify_token(token, token_type="access")
    if payload is None:
        raise credentials_exception

    # Extract claims
    user_id_str = payload.get("sub")
    tenant_id_str = payload.get("tenant_id")
    email = payload.get("email")
    scopes = payload.get("scopes", [])

    if not user_id_str or not tenant_id_str or not email:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        raise credentials_exception

    return Principal(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
        scopes=scopes,
    )


def require_scopes(*required_scopes: str):
    """
    Dependency factory for scope-based authorization

    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_scopes("patients:read"))])
        async def my_endpoint():
            ...

    Args:
        *required_scopes: One or more required permission scopes

    Returns:
        FastAPI dependency function

    Raises:
        HTTPException: If user doesn't have required scopes
    """
    async def check_scopes(principal: Principal = Depends(get_principal)):
        # Check if user has all required scopes
        user_scopes = set(principal.scopes)
        required = set(required_scopes)

        if not required.issubset(user_scopes):
            missing_scopes = required - user_scopes
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing scopes: {', '.join(missing_scopes)}"
            )

        return principal

    return check_scopes


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[Principal]:
    """
    Optional authentication dependency

    Returns Principal if valid token provided, None otherwise.
    Does not raise exception if no token provided.

    Useful for public endpoints that behave differently when authenticated.

    Args:
        credentials: Optional HTTP Authorization header

    Returns:
        Principal if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")
        if payload is None:
            return None

        user_id_str = payload.get("sub")
        tenant_id_str = payload.get("tenant_id")
        email = payload.get("email")
        scopes = payload.get("scopes", [])

        if not user_id_str or not tenant_id_str or not email:
            return None

        user_id = UUID(user_id_str)
        tenant_id = UUID(tenant_id_str)

        return Principal(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            scopes=scopes,
        )
    except Exception:
        return None
