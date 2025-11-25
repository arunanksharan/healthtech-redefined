"""
Insurance & Billing Module

Comprehensive revenue cycle management including:
- Insurance eligibility verification (US-008.1)
- Prior authorization management (US-008.2)
- Claims generation & submission (US-008.3)
- Payment posting & reconciliation (US-008.4)
- Patient billing & collections (US-008.5)
- Fee schedule management (US-008.6)
- Contract management (US-008.7)
- Revenue cycle analytics (US-008.8)
- Compliance & audit (US-008.9)

EPIC-008: Insurance & Billing Integration
"""

from .router import router as billing_router

__all__ = ["billing_router"]
