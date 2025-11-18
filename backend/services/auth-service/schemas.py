"""
Auth Service Pydantic Schemas
Request/Response models for authentication and authorization
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator


# ==================== Authentication Schemas ====================

class LoginRequest(BaseModel):
    """Schema for user login"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    tenant_id: Optional[UUID] = Field(
        None,
        description="Tenant ID (required for multi-tenant users)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "doctor@hospital.com",
                "password": "SecurePassword123!",
                "tenant_id": "00000000-0000-0000-0000-000000000001"
            }
        }


class LoginResponse(BaseModel):
    """Response schema for successful login"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: "UserResponse" = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "user-uuid",
                    "email": "doctor@hospital.com",
                    "full_name": "Dr. Jane Smith"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access token"""

    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordChangeRequest(BaseModel):
    """Schema for changing password"""

    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        }


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset"""

    email: EmailStr = Field(..., description="User email address")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@hospital.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-here",
                "new_password": "NewSecurePassword789!"
            }
        }


# ==================== User Management Schemas ====================

class UserCreate(BaseModel):
    """Schema for creating a user"""

    tenant_id: UUID = Field(..., description="Tenant ID")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role_ids: List[UUID] = Field(
        default_factory=list,
        description="List of role IDs to assign"
    )
    practitioner_id: Optional[UUID] = Field(
        None,
        description="Link to Practitioner entity if applicable"
    )

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "email": "doctor@hospital.com",
                "password": "SecurePassword123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+919876543210",
                "role_ids": ["role-uuid-1"],
                "practitioner_id": "practitioner-uuid"
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Response schema for user"""

    id: UUID
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    practitioner_id: Optional[UUID] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    roles: List["RoleResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "user-uuid",
                "tenant_id": "tenant-uuid",
                "email": "doctor@hospital.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "full_name": "Jane Smith",
                "phone": "+919876543210",
                "is_active": True,
                "practitioner_id": "practitioner-uuid",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
                "roles": []
            }
        }


class UserListResponse(BaseModel):
    """Response schema for list of users"""

    total: int
    users: List[UserResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Role & Permission Schemas ====================

class RoleCreate(BaseModel):
    """Schema for creating a role"""

    tenant_id: UUID = Field(..., description="Tenant ID")
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: List[UUID] = Field(
        default_factory=list,
        description="List of permission IDs"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "name": "senior_doctor",
                "description": "Senior doctor with full clinical access",
                "permission_ids": ["perm-uuid-1", "perm-uuid-2"]
            }
        }


class RoleUpdate(BaseModel):
    """Schema for updating a role"""

    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(BaseModel):
    """Response schema for role"""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    permissions: List["PermissionResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "role-uuid",
                "tenant_id": "tenant-uuid",
                "name": "doctor",
                "description": "Doctor role with clinical access",
                "is_active": True,
                "created_at": "2025-01-15T10:00:00Z",
                "permissions": []
            }
        }


class PermissionCreate(BaseModel):
    """Schema for creating a permission"""

    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(..., description="Resource type (e.g., patient, appointment)")
    action: str = Field(..., description="Action (e.g., read, write, delete)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "patient:write",
                "description": "Create and update patient records",
                "resource": "patient",
                "action": "write"
            }
        }


class PermissionResponse(BaseModel):
    """Response schema for permission"""

    id: UUID
    name: str
    description: Optional[str] = None
    resource: str
    action: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "perm-uuid",
                "name": "patient:write",
                "description": "Create and update patient records",
                "resource": "patient",
                "action": "write",
                "created_at": "2025-01-15T10:00:00Z"
            }
        }


# ==================== Token Validation ====================

class TokenValidationResponse(BaseModel):
    """Response schema for token validation"""

    valid: bool
    user_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "user_id": "user-uuid",
                "tenant_id": "tenant-uuid",
                "email": "user@hospital.com",
                "roles": ["doctor"],
                "permissions": ["patient:read", "patient:write"],
                "expires_at": "2025-01-15T11:00:00Z"
            }
        }
