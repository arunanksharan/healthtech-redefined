"""
Configuration management for PRM Service
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """PRM Service configuration"""

    # Service Info
    APP_NAME: str = "PRM Service"
    VERSION: str = "0.1.0"

    # API Configuration
    API_PREFIX: str = "/api/v1/prm"

    # External Services
    N8N_WEBHOOK_URL: Optional[str] = None

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # Redis Configuration
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Speech-to-Text Configuration
    SPEECH_TO_TEXT_PROVIDER: str = "whisper"  # whisper, google, azure

    # OpenAI Configuration (for Whisper)
    OPENAI_API_KEY: Optional[str] = None

    # S3 Storage Configuration
    S3_BUCKET_NAME: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: Optional[str] = None  # For MinIO/compatible services

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra env vars from .env


settings = Settings()
