"""
Tickets Schemas
Request/Response models for support ticket management
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class TicketPriority(str, Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    """Ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketCreate(BaseModel):
    """Schema for creating a support ticket"""

    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    category: Optional[str] = Field(None, max_length=100)
    assigned_to: Optional[UUID] = None


class TicketUpdate(BaseModel):
    """Schema for updating a ticket"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)


class TicketResponse(BaseModel):
    """Response schema for ticket"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    journey_instance_id: Optional[UUID] = None
    title: str
    description: str
    status: str
    priority: str
    category: Optional[str] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Response for list of tickets"""

    total: int
    tickets: List[TicketResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
