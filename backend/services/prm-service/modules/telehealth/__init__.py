"""
Telehealth Platform Module

Comprehensive telehealth capabilities including:
- Video consultation with WebRTC/LiveKit
- Virtual waiting room management
- Telehealth scheduling with timezone support
- Session recording and compliance
- Screen sharing and collaboration
- In-call clinical tools integration
- Multi-party calls (interpreters)
- Payment processing for telehealth visits

EPIC-007: Telehealth Platform
"""

from .router import router as telehealth_router

__all__ = ["telehealth_router"]
