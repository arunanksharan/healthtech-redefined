"""
Authentication Service
Business logic for user authentication and token management
"""
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from shared.database.models import User, UserRole, RolePermission, Permission
from shared.auth.jwt import create_access_token, create_refresh_token, verify_token
from shared.auth.passwords import verify_password, hash_password
from loguru import logger


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            logger.warning(f"Login attempt for non-existent user: {email}")
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            return None

        # Verify password (assuming User model has hashed_password field)
        if not hasattr(user, 'hashed_password') or not user.hashed_password:
            logger.error(f"User {email} has no password set")
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            return None

        logger.info(f"User authenticated successfully: {email}")
        return user

    def get_user_scopes(self, user_id: UUID) -> list[str]:
        """
        Get all permission scopes for a user

        Args:
            user_id: User ID

        Returns:
            List of permission scope strings
        """
        # Query to get all permissions for user through roles
        # User -> UserRole -> Role -> RolePermission -> Permission

        # Get all roles for user
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id
        ).all()

        if not user_roles:
            logger.warning(f"No roles found for user {user_id}")
            return []

        role_ids = [ur.role_id for ur in user_roles]

        # Get all permissions for these roles
        role_permissions = self.db.query(RolePermission).filter(
            RolePermission.role_id.in_(role_ids)
        ).all()

        if not role_permissions:
            logger.warning(f"No permissions found for user {user_id} roles")
            return []

        permission_ids = [rp.permission_id for rp in role_permissions]

        # Get permission details
        permissions = self.db.query(Permission).filter(
            Permission.id.in_(permission_ids)
        ).all()

        # Extract scope strings
        scopes = [p.scope for p in permissions if p.scope]

        logger.info(f"User {user_id} has scopes: {scopes}")
        return scopes

    def login(self, email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Login user and generate tokens

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (login_response_dict, error_message)
        """
        # Authenticate user
        user = self.authenticate_user(email, password)

        if not user:
            return None, "Invalid email or password"

        # Get user scopes
        scopes = self.get_user_scopes(user.id)

        # Create tokens
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            scopes=scopes,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "scopes": scopes,
        }, None

    def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: JWT refresh token

        Returns:
            Tuple of (new_access_token, error_message)
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")

        if not payload:
            return None, "Invalid or expired refresh token"

        # Extract user_id and tenant_id
        user_id_str = payload.get("sub")
        tenant_id_str = payload.get("tenant_id")

        if not user_id_str or not tenant_id_str:
            return None, "Invalid token payload"

        try:
            user_id = UUID(user_id_str)
            tenant_id = UUID(tenant_id_str)
        except ValueError:
            return None, "Invalid token payload"

        # Get user to verify still active
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return None, "User not found"

        if not user.is_active:
            return None, "User is inactive"

        # Get fresh scopes
        scopes = self.get_user_scopes(user_id)

        # Create new access token
        new_access_token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email=user.email,
            scopes=scopes,
        )

        return new_access_token, None

    def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            Tuple of (success, error_message)
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False, "User not found"

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            return False, "Current password is incorrect"

        # Hash new password
        new_hashed = hash_password(new_password)

        # Update password
        user.hashed_password = new_hashed
        self.db.commit()

        logger.info(f"Password changed for user {user_id}")
        return True, None


def get_auth_service(db: Session) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(db)
