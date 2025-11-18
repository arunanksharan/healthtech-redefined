"""
Auth Service - Authentication and Authorization
JWT-based authentication with RBAC
"""
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, Query, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import Base, User, Role, Permission
from shared.security.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_token_exp_time
)
from shared.security.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_password_reset_token
)
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    TokenValidationResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization with JWT and RBAC",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Authentication ====================

@app.post(
    "/api/v1/auth/login",
    response_model=LoginResponse,
    tags=["Authentication"]
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login with email and password

    Returns JWT access and refresh tokens.
    """
    try:
        # Find user by email
        query = db.query(User).filter(User.email == login_data.email.lower())

        # If tenant_id provided, filter by it
        if login_data.tenant_id:
            query = query.filter(User.tenant_id == login_data.tenant_id)

        user = query.first()

        if not user:
            logger.warning(f"Login attempt for non-existent user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create tokens
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )

        # Get token expiration
        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        logger.info(f"Successful login for user: {user.email}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@app.post(
    "/api/v1/auth/refresh",
    response_model=LoginResponse,
    tags=["Authentication"]
)
async def refresh_token_endpoint(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Returns new access and refresh tokens.
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

        # Get user
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email
        )

        new_refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )

        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@app.post(
    "/api/v1/auth/validate",
    response_model=TokenValidationResponse,
    tags=["Authentication"]
)
async def validate_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Validate access token and return user information

    Used by other services to verify JWT tokens.
    """
    try:
        token = credentials.credentials

        # Verify token
        payload = verify_token(token, token_type="access")

        if not payload:
            return TokenValidationResponse(valid=False)

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

        # Get user with roles and permissions
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()

        if not user:
            return TokenValidationResponse(valid=False)

        # Get roles and permissions
        role_names = [role.name for role in user.roles if role.is_active]
        permissions = set()
        for role in user.roles:
            if role.is_active:
                for perm in role.permissions:
                    permissions.add(perm.name)

        # Get token expiration
        exp_time = get_token_exp_time(token)

        return TokenValidationResponse(
            valid=True,
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            roles=role_names,
            permissions=list(permissions),
            expires_at=exp_time
        )

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return TokenValidationResponse(valid=False)


# ==================== Password Management ====================

@app.post(
    "/api/v1/auth/change-password",
    tags=["Authentication"]
)
async def change_password(
    password_data: PasswordChangeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    try:
        # Verify token
        payload = verify_token(credentials.credentials, token_type="access")

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user_id = UUID(payload["sub"])

        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Validate new password strength
        is_valid, message = validate_password_strength(password_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        # Update password
        user.password_hash = hash_password(password_data.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Password changed for user: {user.email}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@app.post(
    "/api/v1/auth/reset-password/request",
    tags=["Authentication"]
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset

    Generates reset token (in production, this would be sent via email).
    """
    try:
        user = db.query(User).filter(
            User.email == reset_request.email.lower()
        ).first()

        # Don't reveal if user exists
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {reset_request.email}")
            return {
                "message": "If the email exists, a password reset link will be sent"
            }

        # Generate reset token
        reset_token = generate_password_reset_token()

        # Store token in user record (expires in 1 hour)
        # In production, use a separate table or Redis for tokens
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        logger.info(f"Password reset token generated for: {user.email}")

        # TODO: Send email with reset link
        # In production: send_password_reset_email(user.email, reset_token)

        return {
            "message": "If the email exists, a password reset link will be sent",
            "token": reset_token  # Remove this in production!
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@app.post(
    "/api/v1/auth/reset-password/confirm",
    tags=["Authentication"]
)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    try:
        user = db.query(User).filter(
            User.password_reset_token == reset_confirm.token
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        # Check if token expired
        if user.password_reset_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )

        # Validate new password
        is_valid, message = validate_password_strength(reset_confirm.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        # Update password
        user.password_hash = hash_password(reset_confirm.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Password reset completed for: {user.email}")

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# ==================== User Management ====================

@app.post(
    "/api/v1/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"]
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == user_data.email.lower(),
            User.tenant_id == user_data.tenant_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists in this tenant"
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        user = User(
            tenant_id=user_data.tenant_id,
            email=user_data.email.lower(),
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            full_name=f"{user_data.first_name} {user_data.last_name}",
            phone=user_data.phone,
            practitioner_id=user_data.practitioner_id
        )

        db.add(user)
        db.flush()

        # Assign roles
        if user_data.role_ids:
            roles = db.query(Role).filter(
                Role.id.in_(user_data.role_ids),
                Role.tenant_id == user_data.tenant_id
            ).all()
            user.roles = roles

        db.commit()
        db.refresh(user)

        logger.info(f"Created user: {user.email}")

        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@app.get(
    "/api/v1/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"]
)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@app.get(
    "/api/v1/users",
    response_model=UserListResponse,
    tags=["Users"]
)
async def list_users(
    tenant_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List users with filters"""
    try:
        query = db.query(User)

        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        total = query.count()

        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return UserListResponse(
            total=total,
            users=users,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Auth Service starting up...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info("Auth Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004, reload=True)
