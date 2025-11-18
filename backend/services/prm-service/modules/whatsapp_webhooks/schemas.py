"""
WhatsApp Webhooks Schemas
Twilio webhook payload definitions
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MessageStatus(str, Enum):
    """Twilio message status values"""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


class MessageDirection(str, Enum):
    """Message direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ==================== Twilio Webhook Payloads ====================

class TwilioWebhookRequest(BaseModel):
    """
    Incoming message webhook from Twilio WhatsApp

    Twilio sends this when a user sends a message via WhatsApp.
    Field names match Twilio's webhook parameter names exactly.
    """
    # Message identifiers
    MessageSid: str = Field(..., description="Unique message ID from Twilio")
    AccountSid: str = Field(..., description="Twilio account ID")
    MessagingServiceSid: Optional[str] = Field(None, description="Messaging service ID")

    # From/To
    From: str = Field(..., description="Sender phone number (whatsapp:+1234567890)")
    To: str = Field(..., description="Recipient phone number (whatsapp:+1234567890)")

    # Message content
    Body: str = Field(..., description="Message text content")
    NumMedia: str = Field(default="0", description="Number of media attachments")

    # Media (if present)
    MediaUrl0: Optional[str] = Field(None, description="First media URL")
    MediaContentType0: Optional[str] = Field(None, description="First media content type")
    MediaUrl1: Optional[str] = Field(None, description="Second media URL")
    MediaContentType1: Optional[str] = Field(None, description="Second media content type")

    # Profile information
    ProfileName: Optional[str] = Field(None, description="WhatsApp profile name")
    WaId: Optional[str] = Field(None, description="WhatsApp ID")

    # Location (if message contains location)
    Latitude: Optional[str] = Field(None, description="GPS latitude")
    Longitude: Optional[str] = Field(None, description="GPS longitude")

    # Additional metadata
    SmsStatus: Optional[str] = Field(None, description="Message status")
    ApiVersion: Optional[str] = Field(None, description="Twilio API version")

    class Config:
        # Allow extra fields from Twilio that we don't explicitly define
        extra = "allow"


class WhatsAppMessageWebhook(BaseModel):
    """
    Processed WhatsApp message (internal representation)
    """
    message_sid: str
    conversation_id: Optional[str] = None
    patient_id: Optional[str] = None
    direction: MessageDirection
    from_number: str
    to_number: str
    body: str
    media_urls: List[str] = Field(default_factory=list)
    media_types: List[str] = Field(default_factory=list)
    profile_name: Optional[str] = None
    wa_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[MessageStatus] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)


class WhatsAppStatusWebhook(BaseModel):
    """
    Message status update webhook from Twilio

    Twilio sends this when message status changes (sent, delivered, read, failed)
    """
    MessageSid: str
    MessageStatus: str
    AccountSid: str
    From: str
    To: str
    ChannelToAddress: Optional[str] = None
    EventType: Optional[str] = Field(None, description="Event type (e.g., DELIVERED, READ)")
    ErrorCode: Optional[str] = Field(None, description="Error code if failed")
    ErrorMessage: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        extra = "allow"


# ==================== Responses ====================

class TwilioWebhookResponse(BaseModel):
    """
    Response to Twilio webhook

    Twilio expects empty 200 OK response, but we can optionally
    send TwiML to trigger automated responses.
    """
    success: bool
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    actions_taken: List[str] = Field(default_factory=list)


class SendWhatsAppMessageRequest(BaseModel):
    """Request to send a WhatsApp message via Twilio"""
    to: str = Field(..., description="Recipient phone number (E.164 format)")
    body: str = Field(..., description="Message text")
    media_url: Optional[str] = Field(None, description="Media URL to send")
    conversation_id: Optional[str] = Field(None, description="Conversation to associate with")


class SendWhatsAppMessageResponse(BaseModel):
    """Response after sending WhatsApp message"""
    message_sid: str
    status: str
    conversation_id: Optional[str] = None
    to: str
    body: str
