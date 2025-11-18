"""
Permission checking and RBAC (Role-Based Access Control) utilities
"""
from typing import List, Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from loguru import logger

from ..database.connection import get_db
from ..database.models import User, Role, Permission


# Permission constants for common operations
class Permissions:
    """Standard permission definitions"""

    # Patient permissions
    PATIENT_READ = "patient:read"
    PATIENT_WRITE = "patient:write"
    PATIENT_DELETE = "patient:delete"
    PATIENT_MERGE = "patient:merge"

    # Practitioner permissions
    PRACTITIONER_READ = "practitioner:read"
    PRACTITIONER_WRITE = "practitioner:write"
    PRACTITIONER_DELETE = "practitioner:delete"

    # Appointment permissions
    APPOINTMENT_READ = "appointment:read"
    APPOINTMENT_WRITE = "appointment:write"
    APPOINTMENT_CANCEL = "appointment:cancel"

    # Clinical permissions
    ENCOUNTER_READ = "encounter:read"
    ENCOUNTER_WRITE = "encounter:write"
    OBSERVATION_READ = "observation:read"
    OBSERVATION_WRITE = "observation:write"
    ORDER_READ = "order:read"
    ORDER_WRITE = "order:write"
    ORDER_APPROVE = "order:approve"

    # Admin permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    ROLE_MANAGE = "role:manage"
    TENANT_MANAGE = "tenant:manage"

    # System permissions
    SYSTEM_ADMIN = "system:admin"
    AUDIT_READ = "audit:read"


# Standard role definitions
class Roles:
    """Standard role definitions"""

    SYSTEM_ADMIN = "system_admin"
    TENANT_ADMIN = "tenant_admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    PHARMACIST = "pharmacist"
    LAB_TECHNICIAN = "lab_technician"
    PATIENT = "patient"
    CARE_COORDINATOR = "care_coordinator"


def check_permission(
    user_id: str,
    required_permission: str,
    tenant_id: str,
    db: Session
) -> bool:
    """
    Check if a user has a specific permission within a tenant

    Args:
        user_id: UUID of the user
        required_permission: Permission string to check (e.g., "patient:write")
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        bool: True if user has permission, False otherwise

    Example:
        >>> has_perm = check_permission(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     required_permission="patient:write",
        ...     tenant_id="tenant-123",
        ...     db=db_session
        ... )
        >>> print(has_perm)
        True
    """
    try:
        # Get user with roles and permissions
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()

        if not user:
            logger.warning(f"User {user_id} not found or inactive in tenant {tenant_id}")
            return False

        # System admins have all permissions
        if any(role.name == Roles.SYSTEM_ADMIN for role in user.roles):
            logger.debug(f"User {user_id} is system admin, granting permission")
            return True

        # Check if any of the user's roles have the required permission
        for role in user.roles:
            if not role.is_active:
                continue

            for permission in role.permissions:
                if permission.name == required_permission:
                    logger.debug(
                        f"User {user_id} has permission {required_permission} "
                        f"via role {role.name}"
                    )
                    return True

        logger.debug(
            f"User {user_id} does not have permission {required_permission}"
        )
        return False

    except Exception as e:
        logger.error(f"Error checking permission: {e}")
        return False


def check_any_permission(
    user_id: str,
    required_permissions: List[str],
    tenant_id: str,
    db: Session
) -> bool:
    """
    Check if user has ANY of the specified permissions

    Args:
        user_id: UUID of the user
        required_permissions: List of permission strings
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        bool: True if user has at least one permission, False otherwise
    """
    for permission in required_permissions:
        if check_permission(user_id, permission, tenant_id, db):
            return True
    return False


def check_all_permissions(
    user_id: str,
    required_permissions: List[str],
    tenant_id: str,
    db: Session
) -> bool:
    """
    Check if user has ALL of the specified permissions

    Args:
        user_id: UUID of the user
        required_permissions: List of permission strings
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        bool: True if user has all permissions, False otherwise
    """
    for permission in required_permissions:
        if not check_permission(user_id, permission, tenant_id, db):
            return False
    return True


def get_user_permissions(
    user_id: str,
    tenant_id: str,
    db: Session
) -> List[str]:
    """
    Get all permissions for a user within a tenant

    Args:
        user_id: UUID of the user
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        List of permission strings
    """
    try:
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()

        if not user:
            return []

        # System admins have all permissions
        if any(role.name == Roles.SYSTEM_ADMIN for role in user.roles):
            return ["*"]  # Wildcard for all permissions

        permissions = set()
        for role in user.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                permissions.add(permission.name)

        return list(permissions)

    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return []


def require_permission(permission: str):
    """
    Decorator to require a specific permission for an endpoint

    Args:
        permission: Required permission string

    Returns:
        Decorator function

    Example:
        >>> @app.get("/patients")
        >>> @require_permission("patient:read")
        >>> async def get_patients(
        ...     current_user: dict = Depends(get_current_user),
        ...     db: Session = Depends(get_db)
        ... ):
        ...     # Endpoint implementation
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user and db from kwargs
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            user_id = current_user.get("sub")  # User ID from JWT
            tenant_id = current_user.get("tenant_id")

            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )

            # Check permission
            has_permission = check_permission(user_id, permission, tenant_id, db)

            if not has_permission:
                logger.warning(
                    f"Permission denied: User {user_id} attempted to access "
                    f"resource requiring {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )

            # Permission granted, call the original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """
    Decorator to require ANY of the specified permissions

    Args:
        permissions: List of permission strings

    Example:
        >>> @app.get("/clinical-data")
        >>> @require_any_permission(["encounter:read", "observation:read"])
        >>> async def get_clinical_data(...):
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            user_id = current_user.get("sub")
            tenant_id = current_user.get("tenant_id")

            has_permission = check_any_permission(
                user_id, permissions, tenant_id, db
            )

            if not has_permission:
                logger.warning(
                    f"Permission denied: User {user_id} needs one of {permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: One of {permissions} required"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_all_permissions(permissions: List[str]):
    """
    Decorator to require ALL of the specified permissions

    Args:
        permissions: List of permission strings

    Example:
        >>> @app.post("/orders/approve")
        >>> @require_all_permissions(["order:read", "order:approve"])
        >>> async def approve_order(...):
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            user_id = current_user.get("sub")
            tenant_id = current_user.get("tenant_id")

            has_permission = check_all_permissions(
                user_id, permissions, tenant_id, db
            )

            if not has_permission:
                logger.warning(
                    f"Permission denied: User {user_id} needs all of {permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: All of {permissions} required"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: str):
    """
    Decorator to require a specific role

    Args:
        role: Required role name

    Example:
        >>> @app.post("/admin/users")
        >>> @require_role("tenant_admin")
        >>> async def create_user(...):
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )

            user_id = current_user.get("sub")
            tenant_id = current_user.get("tenant_id")

            # Get user's roles
            user = db.query(User).filter(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            has_role = any(r.name == role and r.is_active for r in user.roles)

            if not has_role:
                logger.warning(
                    f"Role check failed: User {user_id} does not have role {role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
