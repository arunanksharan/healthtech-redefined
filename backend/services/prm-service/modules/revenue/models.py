"""
Revenue Infrastructure Models
EPIC-017: Database models for billing and revenue management
"""
from datetime import datetime, date, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, Boolean, DateTime, Date,
    ForeignKey, Index, Enum as SQLEnum, JSON, Numeric, Time, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


# ============================================================================
# Enums
# ============================================================================

class PlanType(str, Enum):
    """Subscription plan types"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(str, Enum):
    """Billing cycle frequency"""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle states"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PaymentMethodType(str, Enum):
    """Types of payment methods"""
    CARD = "card"
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"


class PaymentStatus(str, Enum):
    """Payment transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELED = "canceled"
    DISPUTED = "disputed"


class InvoiceStatus(str, Enum):
    """Invoice lifecycle status"""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    PAST_DUE = "past_due"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class UsageMetricType(str, Enum):
    """Types of usage metrics"""
    AI_INTERACTION = "ai_interaction"
    AI_TOKENS = "ai_tokens"
    TRIAGE_AGENT = "triage_agent"
    SCRIBE_AGENT = "scribe_agent"
    CODING_AGENT = "coding_agent"
    API_CALL = "api_call"
    FHIR_API = "fhir_api"
    TELEHEALTH_MINUTES = "telehealth_minutes"
    SMS_MESSAGE = "sms_message"
    VOICE_MINUTE = "voice_minute"
    WHATSAPP_MESSAGE = "whatsapp_message"
    EMAIL_SEND = "email_send"
    STORAGE_GB = "storage_gb"
    DOCUMENT_PROCESSED = "document_processed"
    ACTIVE_PATIENT = "active_patient"
    ACTIVE_PROVIDER = "active_provider"


class DunningStatus(str, Enum):
    """Dunning workflow status"""
    ACTIVE = "active"
    PAUSED = "paused"
    RECOVERED = "recovered"
    FAILED = "failed"
    CANCELED = "canceled"


class CouponType(str, Enum):
    """Types of discount coupons"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    TRIAL_EXTENSION = "trial_extension"
    FREE_MONTHS = "free_months"


class CreditMemoReason(str, Enum):
    """Reasons for credit memos"""
    SERVICE_ISSUE = "service_issue"
    BILLING_ERROR = "billing_error"
    CUSTOMER_GOODWILL = "customer_goodwill"
    PROMOTION = "promotion"
    DOWNGRADE_PRORATION = "downgrade_proration"
    CANCELLATION = "cancellation"


# ============================================================================
# Plan & Subscription Models
# ============================================================================

class Plan(Base):
    """Subscription plan definition"""
    __tablename__ = "plans"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    plan_type = Column(SQLEnum(PlanType), nullable=False)

    # Pricing
    monthly_price = Column(Numeric(10, 2), nullable=True)
    annual_price = Column(Numeric(10, 2), nullable=True)
    quarterly_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD")

    # Feature limits
    features = Column(JSONB, default=dict)  # Feature flags
    limits = Column(JSONB, default=dict)    # Usage limits
    overage_rates = Column(JSONB, default=dict)  # Overage pricing

    # Trial configuration
    trial_days = Column(Integer, default=14)
    trial_enabled = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Visible on pricing page
    is_legacy = Column(Boolean, default=False)  # Grandfathered plan

    # Metadata
    sort_order = Column(Integer, default=0)
    stripe_product_id = Column(String(100), nullable=True)
    stripe_price_id_monthly = Column(String(100), nullable=True)
    stripe_price_id_annual = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    __table_args__ = (
        Index("idx_plans_slug", "slug"),
        Index("idx_plans_type", "plan_type"),
        Index("idx_plans_active", "is_active"),
    )


class Subscription(Base):
    """Customer subscription"""
    __tablename__ = "subscriptions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)

    # Status
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIALING)
    billing_cycle = Column(SQLEnum(BillingCycle), default=BillingCycle.MONTHLY)

    # Quantities
    quantity = Column(Integer, default=1)  # Number of seats/units
    provider_count = Column(Integer, default=1)
    facility_count = Column(Integer, default=1)

    # Billing info
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Pricing
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    mrr = Column(Numeric(10, 2))  # Monthly recurring revenue
    arr = Column(Numeric(12, 2))  # Annual recurring revenue

    # Stripe integration
    stripe_subscription_id = Column(String(100), nullable=True, index=True)
    stripe_customer_id = Column(String(100), nullable=True, index=True)

    # Metadata
    metadata = Column(JSONB, default=dict)
    cancellation_reason = Column(Text, nullable=True)
    cancellation_feedback = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")

    __table_args__ = (
        Index("idx_subscriptions_tenant", "tenant_id"),
        Index("idx_subscriptions_status", "status"),
        Index("idx_subscriptions_stripe", "stripe_subscription_id"),
    )


class SubscriptionChange(Base):
    """Subscription change history"""
    __tablename__ = "subscription_changes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)

    # Change details
    change_type = Column(String(50), nullable=False)  # upgrade, downgrade, quantity_change, cancel
    from_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    to_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    from_quantity = Column(Integer, nullable=True)
    to_quantity = Column(Integer, nullable=True)

    # Proration
    proration_amount = Column(Numeric(10, 2), default=0)
    proration_credit = Column(Numeric(10, 2), default=0)

    # Timing
    effective_at = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Actor
    changed_by = Column(PGUUID(as_uuid=True), nullable=True)
    change_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_subscription_changes_sub", "subscription_id"),
    )


# ============================================================================
# Payment Models
# ============================================================================

class Customer(Base):
    """Billing customer (maps to tenant)"""
    __tablename__ = "billing_customers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Customer info
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)

    # Billing address
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(2), default="US")

    # Tax info
    tax_id = Column(String(50), nullable=True)  # EIN for US
    tax_exempt = Column(Boolean, default=False)
    tax_exempt_certificate = Column(String(255), nullable=True)

    # Stripe integration
    stripe_customer_id = Column(String(100), nullable=True, unique=True)
    default_payment_method_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Settings
    invoice_settings = Column(JSONB, default=dict)
    payment_terms_days = Column(Integer, default=0)  # Net-0, Net-30, etc.
    currency = Column(String(3), default="USD")

    # Balance
    credit_balance = Column(Numeric(10, 2), default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    payment_methods = relationship("PaymentMethod", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")

    __table_args__ = (
        Index("idx_billing_customers_stripe", "stripe_customer_id"),
    )


class PaymentMethod(Base):
    """Customer payment methods"""
    __tablename__ = "payment_methods"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("billing_customers.id"), nullable=False)

    # Type
    method_type = Column(SQLEnum(PaymentMethodType), nullable=False)
    is_default = Column(Boolean, default=False)

    # Card details (tokenized)
    card_brand = Column(String(20), nullable=True)  # visa, mastercard, amex
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    card_funding = Column(String(20), nullable=True)  # credit, debit

    # Bank account details (for ACH)
    bank_name = Column(String(100), nullable=True)
    bank_last4 = Column(String(4), nullable=True)
    bank_routing_last4 = Column(String(4), nullable=True)
    bank_account_type = Column(String(20), nullable=True)  # checking, savings

    # Stripe integration
    stripe_payment_method_id = Column(String(100), nullable=True, unique=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_status = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="payment_methods")

    __table_args__ = (
        Index("idx_payment_methods_customer", "customer_id"),
        Index("idx_payment_methods_stripe", "stripe_payment_method_id"),
    )


class Payment(Base):
    """Payment transactions"""
    __tablename__ = "payments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("billing_customers.id"), nullable=False)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    payment_method_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_methods.id"), nullable=True)

    # Amount
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    amount_refunded = Column(Numeric(10, 2), default=0)

    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    failure_reason = Column(Text, nullable=True)
    failure_code = Column(String(50), nullable=True)

    # Stripe integration
    stripe_payment_intent_id = Column(String(100), nullable=True, unique=True)
    stripe_charge_id = Column(String(100), nullable=True)

    # Processing details
    processed_at = Column(DateTime(timezone=True), nullable=True)
    receipt_url = Column(String(500), nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_payments_customer", "customer_id"),
        Index("idx_payments_invoice", "invoice_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_stripe", "stripe_payment_intent_id"),
    )


# ============================================================================
# Invoice Models
# ============================================================================

class Invoice(Base):
    """Invoices"""
    __tablename__ = "invoices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("billing_customers.id"), nullable=False)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)

    # Invoice number
    invoice_number = Column(String(50), nullable=False, unique=True)

    # Status
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    amount_due = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Tax details
    tax_rate = Column(Numeric(5, 4), default=0)
    tax_jurisdiction = Column(String(100), nullable=True)

    # Dates
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)

    # Delivery
    pdf_url = Column(String(500), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)

    # Stripe integration
    stripe_invoice_id = Column(String(100), nullable=True, unique=True)

    # Metadata
    memo = Column(Text, nullable=True)
    footer = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice")

    __table_args__ = (
        Index("idx_invoices_tenant", "tenant_id"),
        Index("idx_invoices_customer", "customer_id"),
        Index("idx_invoices_status", "status"),
        Index("idx_invoices_due_date", "due_date"),
        Index("idx_invoices_stripe", "stripe_invoice_id"),
    )


class InvoiceLineItem(Base):
    """Invoice line items"""
    __tablename__ = "invoice_line_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)

    # Description
    description = Column(String(500), nullable=False)
    line_type = Column(String(50), nullable=False)  # subscription, usage, adjustment, tax

    # Amounts
    quantity = Column(Numeric(12, 4), default=1)
    unit_price = Column(Numeric(10, 4), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)

    # Period
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Reference
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    usage_metric_type = Column(SQLEnum(UsageMetricType), nullable=True)

    # Proration
    is_proration = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

    __table_args__ = (
        Index("idx_invoice_line_items_invoice", "invoice_id"),
    )


class CreditMemo(Base):
    """Credit memos for adjustments"""
    __tablename__ = "credit_memos"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("billing_customers.id"), nullable=False)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)

    # Credit memo number
    credit_memo_number = Column(String(50), nullable=False, unique=True)

    # Amount
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    amount_remaining = Column(Numeric(10, 2), nullable=False)

    # Details
    reason = Column(SQLEnum(CreditMemoReason), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_voided = Column(Boolean, default=False)
    voided_at = Column(DateTime(timezone=True), nullable=True)

    # Applied to
    applied_to_invoices = Column(JSONB, default=list)  # List of invoice IDs and amounts

    # Created by
    created_by = Column(PGUUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_credit_memos_tenant", "tenant_id"),
        Index("idx_credit_memos_customer", "customer_id"),
    )


# ============================================================================
# Usage Metering Models
# ============================================================================

class UsageRecord(Base):
    """Usage event records"""
    __tablename__ = "usage_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)

    # Usage details
    metric_type = Column(SQLEnum(UsageMetricType), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(50), nullable=True)

    # Attribution
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    resource_id = Column(String(100), nullable=True)  # API endpoint, feature, etc.

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Billing
    is_billable = Column(Boolean, default=True)
    billed_at = Column(DateTime(timezone=True), nullable=True)
    invoice_line_item_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Metadata
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")

    __table_args__ = (
        Index("idx_usage_records_tenant_metric", "tenant_id", "metric_type"),
        Index("idx_usage_records_recorded", "recorded_at"),
        Index("idx_usage_records_billable", "is_billable", "billed_at"),
    )


class UsageAggregate(Base):
    """Aggregated usage for billing periods"""
    __tablename__ = "usage_aggregates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)

    # Period
    period_type = Column(String(20), nullable=False)  # hourly, daily, monthly
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Metrics
    metric_type = Column(SQLEnum(UsageMetricType), nullable=False)
    total_quantity = Column(Numeric(14, 4), nullable=False)
    record_count = Column(Integer, nullable=False)

    # Billing
    included_quantity = Column(Numeric(14, 4), default=0)
    overage_quantity = Column(Numeric(14, 4), default=0)
    overage_rate = Column(Numeric(10, 4), default=0)
    overage_amount = Column(Numeric(10, 2), default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_usage_aggregates_tenant_period", "tenant_id", "period_start", "period_end"),
        Index("idx_usage_aggregates_metric", "metric_type", "period_start"),
        UniqueConstraint("tenant_id", "metric_type", "period_type", "period_start",
                         name="uq_usage_aggregates_period"),
    )


# ============================================================================
# Dunning Models
# ============================================================================

class DunningCampaign(Base):
    """Dunning campaign for failed payments"""
    __tablename__ = "dunning_campaigns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)

    # Status
    status = Column(SQLEnum(DunningStatus), default=DunningStatus.ACTIVE)

    # Failed payment
    failed_payment_id = Column(PGUUID(as_uuid=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    original_failure_at = Column(DateTime(timezone=True), nullable=False)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=4)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Notifications
    notifications_sent = Column(Integer, default=0)
    last_notification_at = Column(DateTime(timezone=True), nullable=True)
    notification_history = Column(JSONB, default=list)

    # Grace period
    grace_period_ends_at = Column(DateTime(timezone=True), nullable=False)
    is_in_grace_period = Column(Boolean, default=True)

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_type = Column(String(50), nullable=True)  # payment_success, manual, canceled
    successful_payment_id = Column(PGUUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_dunning_campaigns_tenant", "tenant_id"),
        Index("idx_dunning_campaigns_status", "status"),
        Index("idx_dunning_campaigns_next_retry", "next_retry_at"),
    )


# ============================================================================
# Coupon & Discount Models
# ============================================================================

class Coupon(Base):
    """Discount coupons"""
    __tablename__ = "coupons"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Discount type
    coupon_type = Column(SQLEnum(CouponType), nullable=False)
    discount_percent = Column(Numeric(5, 2), nullable=True)
    discount_amount = Column(Numeric(10, 2), nullable=True)
    trial_extension_days = Column(Integer, nullable=True)
    free_months = Column(Integer, nullable=True)

    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    max_redemptions = Column(Integer, nullable=True)
    redemption_count = Column(Integer, default=0)
    max_redemptions_per_customer = Column(Integer, default=1)

    # Restrictions
    applicable_plans = Column(ARRAY(PGUUID(as_uuid=True)), nullable=True)
    min_subscription_amount = Column(Numeric(10, 2), nullable=True)
    first_time_only = Column(Boolean, default=False)

    # Duration
    duration = Column(String(20), default="once")  # once, repeating, forever
    duration_months = Column(Integer, nullable=True)

    # Stripe integration
    stripe_coupon_id = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_coupons_code", "code"),
        Index("idx_coupons_active", "is_active"),
    )


class CouponRedemption(Base):
    """Coupon redemption records"""
    __tablename__ = "coupon_redemptions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    coupon_id = Column(PGUUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)

    # Discount applied
    discount_amount = Column(Numeric(10, 2), nullable=False)
    remaining_applications = Column(Integer, nullable=True)

    # Validity
    redeemed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_coupon_redemptions_tenant", "tenant_id"),
        Index("idx_coupon_redemptions_coupon", "coupon_id"),
    )


# ============================================================================
# Revenue Recognition Models
# ============================================================================

class RevenueSchedule(Base):
    """Revenue recognition schedule"""
    __tablename__ = "revenue_schedules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    invoice_line_item_id = Column(PGUUID(as_uuid=True), ForeignKey("invoice_line_items.id"), nullable=True)

    # Schedule details
    total_amount = Column(Numeric(10, 2), nullable=False)
    recognized_amount = Column(Numeric(10, 2), default=0)
    deferred_amount = Column(Numeric(10, 2), nullable=False)

    # Period
    recognition_start = Column(Date, nullable=False)
    recognition_end = Column(Date, nullable=False)
    recognition_method = Column(String(50), default="straight_line")  # straight_line, usage_based

    # Status
    is_complete = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_revenue_schedules_tenant", "tenant_id"),
        Index("idx_revenue_schedules_period", "recognition_start", "recognition_end"),
    )


class RevenueRecognition(Base):
    """Individual revenue recognition entries"""
    __tablename__ = "revenue_recognitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    schedule_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_schedules.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Recognition period
    period_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    # Journal entry reference
    journal_entry_id = Column(String(100), nullable=True)
    exported_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_revenue_recognitions_schedule", "schedule_id"),
        Index("idx_revenue_recognitions_period", "period_date"),
    )


# ============================================================================
# Entitlement Models
# ============================================================================

class Entitlement(Base):
    """Feature entitlements per subscription"""
    __tablename__ = "entitlements"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)

    # Feature
    feature_key = Column(String(100), nullable=False)
    feature_name = Column(String(200), nullable=False)

    # Limits
    limit_type = Column(String(20), nullable=False)  # boolean, count, unlimited
    limit_value = Column(Integer, nullable=True)
    current_usage = Column(Integer, default=0)

    # Status
    is_enabled = Column(Boolean, default=True)

    # Override
    is_override = Column(Boolean, default=False)
    override_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_entitlements_tenant", "tenant_id"),
        Index("idx_entitlements_feature", "feature_key"),
        UniqueConstraint("subscription_id", "feature_key", name="uq_entitlements_sub_feature"),
    )


# ============================================================================
# Audit Models
# ============================================================================

class BillingAuditLog(Base):
    """Billing audit trail"""
    __tablename__ = "billing_audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Actor
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    actor_type = Column(String(50), nullable=False)  # user, system, stripe_webhook

    # Action
    action = Column(String(100), nullable=False)
    action_category = Column(String(50), nullable=False)  # subscription, payment, invoice, usage
    action_description = Column(Text, nullable=True)

    # Resource
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Changes
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_billing_audit_tenant", "tenant_id"),
        Index("idx_billing_audit_action", "action"),
        Index("idx_billing_audit_resource", "resource_type", "resource_id"),
        Index("idx_billing_audit_created", "created_at"),
    )
