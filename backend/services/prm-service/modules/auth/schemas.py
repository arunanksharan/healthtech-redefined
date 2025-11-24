"""
Authentication Schemas
Pydantic models for authentication requests and responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List
from uuid import UUID


class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
    """Login response with tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: UUID = Field(..., description="User ID")
    tenant_id: UUID = Field(..., description="Organization/tenant ID")
    email: str = Field(..., description="User email")
    scopes: List[str] = Field(..., description="User permission scopes")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response with new access token"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: str = Field(..., description="JWT refresh token to invalidate")


class LogoutResponse(BaseModel):
    """Logout response"""
    message: str = Field(default="Successfully logged out", description="Logout message")


class CurrentUserResponse(BaseModel):
    """Current user information"""
    user_id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    scopes: List[str]
    is_active: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")


class ChangePasswordResponse(BaseModel):
    """Change password response"""
    message: str = Field(default="Password changed successfully")
