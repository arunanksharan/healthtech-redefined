"""
Authentication Router
API endpoints for user authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared.database.connection import get_db
from shared.database.models import User
from shared.auth.dependencies import get_current_user, get_principal, Principal

from .schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    CurrentUserResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
)
from .service import AuthService, get_auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Login with email and password

    Returns JWT access token and refresh token.

    **Example Request:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePassword123"
    }
    ```

    **Example Response:**
    ```json
    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer",
      "user_id": "uuid",
      "tenant_id": "uuid",
      "email": "user@example.com",
      "scopes": ["patients:read", "appointments:write"]
    }
    ```

    **Authentication Flow:**
    1. Validate email and password
    2. Check user is active
    3. Get user permissions (scopes)
    4. Generate access token (30 min expiry)
    5. Generate refresh token (7 day expiry)
    6. Return tokens to client

    **Next Steps:**
    - Store tokens securely in client (httpOnly cookie or secure storage)
    - Include access token in Authorization header: `Bearer <token>`
    - Use refresh token to get new access token when expired
    """
    result, error = service.login(request.email, request.password)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using refresh token

    **Example Request:**
    ```json
    {
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    ```

    **Example Response:**
    ```json
    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer"
    }
    ```

    **When to Use:**
    - Access token expired (401 Unauthorized response)
    - Preemptively before access token expires
    - Access token has less than 5 minutes remaining

    **Security Notes:**
    - Refresh tokens have longer expiry (7 days)
    - Access tokens have short expiry (30 minutes)
    - If refresh token expired, user must login again
    """
    new_access_token, error = service.refresh_access_token(request.refresh_token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    principal: Principal = Depends(get_principal),
):
    """
    Logout user

    **Note:** JWT tokens are stateless and cannot be invalidated server-side
    without additional infrastructure (Redis blacklist, etc.).

    For basic logout:
    1. Client deletes tokens from storage
    2. Client clears user session

    For secure logout (future enhancement):
    1. Add token to Redis blacklist
    2. Check blacklist on each request
    3. Tokens expire after TTL

    **Current Implementation:**
    - Client-side token deletion
    - Server validates token exists and belongs to user
    - Returns success message

    **Security Note:**
    Until blacklisting is implemented, tokens remain valid until expiry.
    Ensure access tokens have short expiry times (30 minutes).
    """
    return {
        "message": "Successfully logged out. Please delete tokens from client storage."
    }


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Get current authenticated user information

    Returns detailed information about the currently logged-in user.

    **Example Response:**
    ```json
    {
      "user_id": "uuid",
      "tenant_id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "doctor",
      "scopes": ["patients:read", "appointments:write"],
      "is_active": true
    }
    ```

    **Use Cases:**
    - Display user profile in UI
    - Check user permissions client-side
    - Verify authentication is still valid
    - Get user context for logging/analytics
    """
    # Get user scopes
    scopes = service.get_user_scopes(user.id)

    return {
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "scopes": scopes,
        "is_active": user.is_active,
    }


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    principal: Principal = Depends(get_principal),
    service: AuthService = Depends(get_auth_service),
):
    """
    Change user password

    **Example Request:**
    ```json
    {
      "current_password": "OldPassword123",
      "new_password": "NewSecurePassword456",
      "confirm_password": "NewSecurePassword456"
    }
    ```

    **Validation:**
    - Current password must be correct
    - New password must be at least 8 characters
    - New password must match confirm password
    - New password must be different from current

    **Security:**
    - Requires authentication (current access token)
    - Verifies current password before change
    - Hashes new password with bcrypt
    - Invalidates current sessions (future enhancement)
    """
    # Validate new password matches confirm
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match"
        )

    # Validate new password is different from current
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Change password
    success, error = service.change_password(
        user_id=principal.user_id,
        current_password=request.current_password,
        new_password=request.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Failed to change password"
        )

    return {
        "message": "Password changed successfully"
    }
