"""
Twilio client for WhatsApp messaging
"""
from typing import Optional
from loguru import logger

# Optional Twilio support
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    Client = None  # type: ignore
    TWILIO_AVAILABLE = False
    logger.warning("twilio package not installed, WhatsApp messaging disabled")

from .config import settings


class TwilioClientWrapper:
    """Twilio client wrapper"""

    def __init__(self):
        self.client: Optional[Client] = None
        self.phone_number: Optional[str] = None
        self._initialize()

    def _initialize(self):
        """Initialize Twilio client"""
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio library not available")
            return

        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                self.phone_number = settings.TWILIO_PHONE_NUMBER
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            logger.warning("Twilio credentials not configured")

    def send_message(self, to: str, body: str) -> bool:
        """Send WhatsApp message"""
        if not self.client or not self.phone_number:
            logger.warning("Twilio client not available, cannot send message")
            return False

        try:
            message = self.client.messages.create(
                body=body,
                from_=f"whatsapp:{self.phone_number}",
                to=f"whatsapp:{to}"
            )
            logger.info(f"Sent WhatsApp message {message.sid} to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False


# Global Twilio client instance
twilio_client = TwilioClientWrapper()
