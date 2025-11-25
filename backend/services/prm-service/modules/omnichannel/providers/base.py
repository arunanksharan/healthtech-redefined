"""
Base Channel Provider Interface
Abstract base class for all communication channel providers
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID
import asyncio
from loguru import logger


class ProviderStatus(str, Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ProviderResult:
    """Result from provider operation"""
    success: bool
    external_id: Optional[str] = None
    status: str = "sent"
    cost: Optional[float] = None
    segments: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_retriable: bool = False


class ProviderError(Exception):
    """Provider operation error"""
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        is_retriable: bool = False,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.is_retriable = is_retriable
        self.original_error = original_error


@dataclass
class MessagePayload:
    """Standardized message payload"""
    recipient: str
    content: Optional[str] = None
    subject: Optional[str] = None
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    buttons: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)


@dataclass
class WebhookPayload:
    """Standardized webhook payload"""
    raw_data: Dict[str, Any]
    message_id: Optional[str] = None
    status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    content: Optional[str] = None
    content_type: str = "text"
    attachments: List[Dict[str, Any]] = field(default_factory=list)


class BaseChannelProvider(ABC):
    """
    Abstract base class for all channel providers.
    Each provider implements channel-specific communication logic.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration including credentials
        """
        self.config = config
        self.provider_id: Optional[UUID] = config.get('provider_id')
        self.tenant_id: Optional[UUID] = config.get('tenant_id')
        self.is_initialized = False
        self.last_health_check: Optional[datetime] = None
        self.health_status = ProviderStatus.HEALTHY
        self.failure_count = 0
        self.rate_limiter = RateLimiter(
            max_per_second=config.get('rate_limit_per_second', 10),
            max_per_day=config.get('rate_limit_per_day')
        )

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider (authenticate, setup connections, etc.)
        Returns True if successful.
        """
        pass

    @abstractmethod
    async def send_message(self, payload: MessagePayload) -> ProviderResult:
        """
        Send a message through this channel.

        Args:
            payload: Standardized message payload

        Returns:
            ProviderResult with delivery status
        """
        pass

    @abstractmethod
    async def send_template(
        self,
        recipient: str,
        template_name: str,
        variables: Dict[str, Any],
        language: str = "en"
    ) -> ProviderResult:
        """
        Send a pre-approved template message.

        Args:
            recipient: Message recipient
            template_name: Template identifier
            variables: Template variable values
            language: Template language code

        Returns:
            ProviderResult with delivery status
        """
        pass

    @abstractmethod
    async def parse_webhook(self, data: Dict[str, Any]) -> WebhookPayload:
        """
        Parse incoming webhook data into standardized format.

        Args:
            data: Raw webhook payload

        Returns:
            Standardized WebhookPayload
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify webhook signature for security.

        Args:
            payload: Raw request body
            signature: Signature from headers
            timestamp: Optional timestamp for replay protection

        Returns:
            True if signature is valid
        """
        pass

    async def health_check(self) -> ProviderStatus:
        """
        Check provider health status.
        Override for provider-specific health checks.
        """
        self.last_health_check = datetime.utcnow()
        return self.health_status

    async def send_with_retry(
        self,
        payload: MessagePayload,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> ProviderResult:
        """
        Send message with automatic retry on failure.

        Args:
            payload: Message payload
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (exponential backoff)

        Returns:
            ProviderResult
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Check rate limit
                if not await self.rate_limiter.check():
                    raise ProviderError(
                        "Rate limit exceeded",
                        error_code="RATE_LIMIT",
                        is_retriable=True
                    )

                result = await self.send_message(payload)

                if result.success:
                    self.failure_count = 0
                    return result

                if not result.is_retriable:
                    return result

                last_error = ProviderError(
                    result.error_message or "Send failed",
                    error_code=result.error_code,
                    is_retriable=result.is_retriable
                )

            except ProviderError as e:
                last_error = e
                if not e.is_retriable:
                    self.failure_count += 1
                    raise

            except Exception as e:
                last_error = ProviderError(
                    str(e),
                    error_code="UNKNOWN",
                    is_retriable=True,
                    original_error=e
                )

            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    f"Provider send failed, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

        self.failure_count += 1

        return ProviderResult(
            success=False,
            error_code=last_error.error_code if last_error else "UNKNOWN",
            error_message=str(last_error) if last_error else "Max retries exceeded",
            is_retriable=False
        )

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient format for this channel.
        Override for channel-specific validation.
        """
        return bool(recipient and len(recipient) >= 3)

    def format_phone_number(self, phone: str, default_country: str = "US") -> str:
        """
        Format phone number to E.164 format.

        Args:
            phone: Raw phone number
            default_country: Default country code if not provided

        Returns:
            E.164 formatted phone number
        """
        # Remove common formatting characters
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Add + if not present
        if not cleaned.startswith('+'):
            # Assume US if no country code
            if len(cleaned) == 10:
                cleaned = f"+1{cleaned}"
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = f"+{cleaned}"
            else:
                cleaned = f"+{cleaned}"

        return cleaned

    def get_message_cost(self, payload: MessagePayload) -> float:
        """
        Estimate message cost based on channel and content.
        Override for provider-specific pricing.
        """
        return 0.0

    def get_segments_count(self, content: str) -> int:
        """
        Calculate number of message segments (for SMS).
        """
        if not content:
            return 1

        # GSM-7 character set allows 160 chars per segment
        # Unicode allows 70 chars per segment
        gsm7_chars = set(
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ ÆæßÉ!\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
        )

        is_gsm7 = all(c in gsm7_chars for c in content)
        max_per_segment = 160 if is_gsm7 else 70

        return (len(content) + max_per_segment - 1) // max_per_segment


class RateLimiter:
    """Simple rate limiter for provider requests"""

    def __init__(self, max_per_second: int = 10, max_per_day: Optional[int] = None):
        self.max_per_second = max_per_second
        self.max_per_day = max_per_day
        self.requests = []
        self.daily_count = 0
        self.last_reset = datetime.utcnow().date()

    async def check(self) -> bool:
        """Check if request is allowed under rate limits"""
        now = datetime.utcnow()

        # Reset daily counter if needed
        if now.date() != self.last_reset:
            self.daily_count = 0
            self.last_reset = now.date()

        # Check daily limit
        if self.max_per_day and self.daily_count >= self.max_per_day:
            return False

        # Clean old requests (outside 1-second window)
        self.requests = [
            r for r in self.requests
            if (now - r).total_seconds() < 1
        ]

        # Check per-second limit
        if len(self.requests) >= self.max_per_second:
            return False

        self.requests.append(now)
        self.daily_count += 1
        return True

    async def wait_if_needed(self) -> None:
        """Wait until rate limit allows next request"""
        while not await self.check():
            await asyncio.sleep(0.1)
