"""
Authentication and Authorization Module
Provides JWT handling, password hashing, and security utilities
"""

from .jwt import create_access_token, create_refresh_token, verify_token, decode_token
from .passwords import hash_password, verify_password
from .dependencies import get_current_user, get_principal, require_scopes, Principal

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    "hash_password",
    "verify_password",
    "get_current_user",
    "get_principal",
    "require_scopes",
    "Principal",
]
