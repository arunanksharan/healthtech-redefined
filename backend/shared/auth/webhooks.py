"""
Webhook Security Utilities
Provides signature verification for webhook endpoints
"""
import os
import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException, status
from loguru import logger


def verify_webhook_secret(
    provided_secret: str,
    expected_secret_env_var: str,
    service_name: str = "webhook",
) -> bool:
    """
    Verify webhook secret against environment variable

    Args:
        provided_secret: Secret provided in request header
        expected_secret_env_var: Name of environment variable containing expected secret
        service_name: Name of service for logging

    Returns:
        True if valid

    Raises:
        HTTPException: If secret is invalid or not configured
    """
    expected_secret = os.getenv(expected_secret_env_var)

    if not expected_secret:
        logger.error(
            f"{service_name} webhook secret not configured. "
            f"Set {expected_secret_env_var} environment variable."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{service_name} webhook authentication not configured"
        )

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_secret, expected_secret):
        logger.warning(f"Invalid {service_name} webhook secret provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret"
        )

    return True


def verify_twilio_signature(
    signature: str,
    url: str,
    params: dict,
    auth_token: Optional[str] = None,
) -> bool:
    """
    Verify Twilio webhook signature

    Twilio signs all webhook requests to verify they came from Twilio.

    Args:
        signature: X-Twilio-Signature header value
        url: Full URL of the webhook endpoint (including protocol and domain)
        params: POST parameters as dict
        auth_token: Twilio auth token (from env if not provided)

    Returns:
        True if valid

    Raises:
        HTTPException: If signature is invalid

    Reference:
        https://www.twilio.com/docs/usage/security#validating-requests
    """
    if not auth_token:
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not auth_token:
        logger.error("Twilio auth token not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Twilio authentication not configured"
        )

    # Build data string: URL + sorted params
    data = url
    for key in sorted(params.keys()):
        data += key + params[key]

    # Compute HMAC-SHA1
    computed_signature = hmac.new(
        auth_token.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha1
    ).digest()

    # Base64 encode
    import base64
    computed_signature_b64 = base64.b64encode(computed_signature).decode('utf-8')

    # Compare signatures
    if not hmac.compare_digest(signature, computed_signature_b64):
        logger.warning("Invalid Twilio signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    return True


def verify_api_key(
    provided_key: str,
    expected_key_env_var: str = "API_KEY",
    service_name: str = "API",
) -> bool:
    """
    Verify API key against environment variable

    Args:
        provided_key: API key provided in X-API-Key header
        expected_key_env_var: Name of environment variable containing expected key
        service_name: Name of service for logging

    Returns:
        True if valid

    Raises:
        HTTPException: If API key is invalid or not configured
    """
    expected_key = os.getenv(expected_key_env_var)

    if not expected_key:
        logger.error(
            f"{service_name} API key not configured. "
            f"Set {expected_key_env_var} environment variable."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{service_name} authentication not configured"
        )

    # Use constant-time comparison
    if not hmac.compare_digest(provided_key, expected_key):
        logger.warning(f"Invalid {service_name} API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return True
