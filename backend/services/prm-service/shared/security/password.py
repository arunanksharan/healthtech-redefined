"""
Password hashing and verification utilities
Using bcrypt for secure password hashing
"""
from passlib.context import CryptContext
from loguru import logger

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Number of hashing rounds (higher = more secure but slower)
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> print(hashed)
        $2b$12$...
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    if not plain_password or not hashed_password:
        logger.warning("Empty password or hash provided for verification")
        return False

    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)

        if is_valid:
            logger.debug("Password verification successful")

            # Check if password needs rehashing (if bcrypt rounds have been updated)
            if pwd_context.needs_update(hashed_password):
                logger.info("Password hash needs update to newer algorithm")
        else:
            logger.debug("Password verification failed")

        return is_valid
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength against security requirements

    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    - Contains special character

    Args:
        password: Password to validate

    Returns:
        tuple: (is_valid: bool, message: str)

    Example:
        >>> is_valid, msg = validate_password_strength("Weak1")
        >>> print(is_valid, msg)
        False "Password must be at least 8 characters long"

        >>> is_valid, msg = validate_password_strength("SecureP@ss123")
        >>> print(is_valid, msg)
        True "Password meets all requirements"
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not has_upper:
        return False, "Password must contain at least one uppercase letter"

    if not has_lower:
        return False, "Password must contain at least one lowercase letter"

    if not has_digit:
        return False, "Password must contain at least one digit"

    if not has_special:
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"

    return True, "Password meets all requirements"


def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password reset

    Returns:
        str: Random token (32 bytes, hex encoded = 64 characters)

    Example:
        >>> token = generate_password_reset_token()
        >>> len(token)
        64
    """
    import secrets
    token = secrets.token_hex(32)
    logger.debug("Password reset token generated")
    return token
