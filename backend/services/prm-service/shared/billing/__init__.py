"""
Insurance & Billing Module

Comprehensive revenue cycle management including:
- Insurance eligibility verification
- Claims management and submission
- Payment processing
- Explanation of Benefits (EOB)
- Patient billing and statements

EPIC-008: Insurance & Billing System
"""

from .eligibility import (
    EligibilityService,
    EligibilityCheck,
    CoverageInfo,
    BenefitInfo,
)
from .claims import (
    ClaimsService,
    Claim,
    ClaimLine,
    ClaimStatus,
)
from .payments import (
    PaymentService,
    Payment,
    PaymentMethod,
    PaymentStatus,
)

__all__ = [
    # Eligibility
    "EligibilityService",
    "EligibilityCheck",
    "CoverageInfo",
    "BenefitInfo",
    # Claims
    "ClaimsService",
    "Claim",
    "ClaimLine",
    "ClaimStatus",
    # Payments
    "PaymentService",
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
]
