"""
Revenue Infrastructure Module
EPIC-017: Billing, Payments, and Revenue Management

This module provides:
- Subscription management with plan lifecycle
- Usage metering for AI and platform features
- Stripe payment processing
- Invoice generation
- Dunning and collections
- Revenue recognition (ASC 606)
- Customer billing portal
- SaaS metrics and analytics
"""

from modules.revenue.router import router
from modules.revenue.models import (
    Plan, Subscription, SubscriptionChange,
    Customer, PaymentMethod, Payment,
    Invoice, InvoiceLineItem, CreditMemo,
    UsageRecord, UsageAggregate,
    DunningCampaign, Coupon, CouponRedemption,
    RevenueSchedule, RevenueRecognition,
    Entitlement, BillingAuditLog
)
from modules.revenue.services import (
    SubscriptionService,
    UsageMeteringService,
    PaymentService,
    InvoiceService,
    DunningService,
    RevenueService
)

__all__ = [
    # Router
    "router",
    # Models
    "Plan",
    "Subscription",
    "SubscriptionChange",
    "Customer",
    "PaymentMethod",
    "Payment",
    "Invoice",
    "InvoiceLineItem",
    "CreditMemo",
    "UsageRecord",
    "UsageAggregate",
    "DunningCampaign",
    "Coupon",
    "CouponRedemption",
    "RevenueSchedule",
    "RevenueRecognition",
    "Entitlement",
    "BillingAuditLog",
    # Services
    "SubscriptionService",
    "UsageMeteringService",
    "PaymentService",
    "InvoiceService",
    "DunningService",
    "RevenueService"
]
