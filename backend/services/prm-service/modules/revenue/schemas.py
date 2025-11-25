"""
Revenue Infrastructure Schemas
EPIC-017: Pydantic schemas for billing and revenue API
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enum Schemas
# ============================================================================

class PlanTypeSchema(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycleSchema(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class SubscriptionStatusSchema(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PaymentMethodTypeSchema(str, Enum):
    CARD = "card"
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"


class PaymentStatusSchema(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELED = "canceled"
    DISPUTED = "disputed"


class InvoiceStatusSchema(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    PAST_DUE = "past_due"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class UsageMetricTypeSchema(str, Enum):
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


class CouponTypeSchema(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    TRIAL_EXTENSION = "trial_extension"
    FREE_MONTHS = "free_months"


class CreditMemoReasonSchema(str, Enum):
    SERVICE_ISSUE = "service_issue"
    BILLING_ERROR = "billing_error"
    CUSTOMER_GOODWILL = "customer_goodwill"
    PROMOTION = "promotion"
    DOWNGRADE_PRORATION = "downgrade_proration"
    CANCELLATION = "cancellation"


# ============================================================================
# Plan Schemas
# ============================================================================

class PlanFeatures(BaseModel):
    """Plan feature configuration"""
    patients: Optional[int] = None
    providers: Optional[int] = None
    facilities: Optional[int] = None
    ai_interactions: Optional[int] = None
    telehealth_minutes: Optional[int] = None
    sms_messages: Optional[int] = None
    fhir_api_calls: Optional[int] = None
    storage_gb: Optional[int] = None
    ambient_scribe: Optional[bool] = False
    coding_agent: Optional[bool] = False
    custom_integrations: Optional[bool] = False
    dedicated_support: Optional[bool] = False
    sla_guarantee: Optional[str] = None
    hipaa_baa: Optional[bool] = False


class PlanOverageRates(BaseModel):
    """Overage pricing per unit"""
    ai_interactions: Optional[float] = None
    telehealth_minutes: Optional[float] = None
    sms_messages: Optional[float] = None
    storage_gb: Optional[float] = None


class PlanCreate(BaseModel):
    """Create a new plan"""
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=50)
    description: Optional[str] = None
    plan_type: PlanTypeSchema
    monthly_price: Optional[Decimal] = None
    annual_price: Optional[Decimal] = None
    quarterly_price: Optional[Decimal] = None
    currency: str = "USD"
    features: Optional[PlanFeatures] = None
    limits: Optional[Dict[str, int]] = None
    overage_rates: Optional[PlanOverageRates] = None
    trial_days: int = 14
    trial_enabled: bool = True
    is_public: bool = True


class PlanUpdate(BaseModel):
    """Update plan details"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    monthly_price: Optional[Decimal] = None
    annual_price: Optional[Decimal] = None
    quarterly_price: Optional[Decimal] = None
    features: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, int]] = None
    overage_rates: Optional[Dict[str, float]] = None
    trial_days: Optional[int] = None
    trial_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanResponse(BaseModel):
    """Plan response"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    plan_type: str
    monthly_price: Optional[float]
    annual_price: Optional[float]
    quarterly_price: Optional[float]
    currency: str
    features: Dict[str, Any]
    limits: Dict[str, Any]
    overage_rates: Dict[str, Any]
    trial_days: int
    trial_enabled: bool
    is_active: bool
    is_public: bool
    is_legacy: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    """List of plans"""
    plans: List[PlanResponse]
    total: int


class PlanComparisonResponse(BaseModel):
    """Plan comparison for pricing page"""
    plans: List[PlanResponse]
    feature_matrix: Dict[str, Dict[str, Any]]


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionCreate(BaseModel):
    """Create a new subscription"""
    plan_id: UUID
    billing_cycle: BillingCycleSchema = BillingCycleSchema.MONTHLY
    quantity: int = 1
    provider_count: int = 1
    facility_count: int = 1
    coupon_code: Optional[str] = None
    payment_method_id: Optional[UUID] = None
    start_trial: bool = True
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionUpdate(BaseModel):
    """Update subscription"""
    quantity: Optional[int] = None
    provider_count: Optional[int] = None
    facility_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionChangePlan(BaseModel):
    """Change subscription plan"""
    new_plan_id: UUID
    billing_cycle: Optional[BillingCycleSchema] = None
    prorate: bool = True
    effective_immediately: bool = True


class SubscriptionCancel(BaseModel):
    """Cancel subscription"""
    reason: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    cancel_at_period_end: bool = True


class SubscriptionResponse(BaseModel):
    """Subscription response"""
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    plan_name: Optional[str] = None
    status: str
    billing_cycle: str
    quantity: int
    provider_count: int
    facility_count: int
    unit_price: float
    discount_percent: float
    mrr: Optional[float]
    arr: Optional[float]
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """List of subscriptions"""
    subscriptions: List[SubscriptionResponse]
    total: int


class ProrationPreview(BaseModel):
    """Proration preview for plan change"""
    current_plan: str
    new_plan: str
    proration_amount: float
    proration_credit: float
    net_amount: float
    effective_date: datetime
    next_billing_date: datetime


# ============================================================================
# Customer Schemas
# ============================================================================

class CustomerCreate(BaseModel):
    """Create billing customer"""
    name: str = Field(..., max_length=200)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: str = "US"
    tax_id: Optional[str] = None
    tax_exempt: bool = False
    payment_terms_days: int = 0
    currency: str = "USD"


class CustomerUpdate(BaseModel):
    """Update billing customer"""
    name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = None
    billing_address_line1: Optional[str] = None
    billing_address_line2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    tax_id: Optional[str] = None
    tax_exempt: Optional[bool] = None
    payment_terms_days: Optional[int] = None


class CustomerResponse(BaseModel):
    """Customer response"""
    id: UUID
    tenant_id: UUID
    name: str
    email: str
    phone: Optional[str]
    billing_address_line1: Optional[str]
    billing_address_line2: Optional[str]
    billing_city: Optional[str]
    billing_state: Optional[str]
    billing_postal_code: Optional[str]
    billing_country: str
    tax_id: Optional[str]
    tax_exempt: bool
    stripe_customer_id: Optional[str]
    credit_balance: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Payment Method Schemas
# ============================================================================

class PaymentMethodCreate(BaseModel):
    """Create payment method (with Stripe token)"""
    method_type: PaymentMethodTypeSchema
    stripe_payment_method_token: str  # From Stripe.js
    set_as_default: bool = True


class PaymentMethodResponse(BaseModel):
    """Payment method response"""
    id: UUID
    method_type: str
    is_default: bool
    card_brand: Optional[str]
    card_last4: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    card_funding: Optional[str]
    bank_name: Optional[str]
    bank_last4: Optional[str]
    bank_account_type: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    """List of payment methods"""
    payment_methods: List[PaymentMethodResponse]
    default_id: Optional[UUID]


# ============================================================================
# Payment Schemas
# ============================================================================

class PaymentCreate(BaseModel):
    """Create a payment"""
    amount: Decimal
    payment_method_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    description: Optional[str] = None


class PaymentRefund(BaseModel):
    """Refund a payment"""
    amount: Optional[Decimal] = None  # None = full refund
    reason: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response"""
    id: UUID
    customer_id: UUID
    invoice_id: Optional[UUID]
    amount: float
    currency: str
    amount_refunded: float
    status: str
    failure_reason: Optional[str]
    receipt_url: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """List of payments"""
    payments: List[PaymentResponse]
    total: int


# ============================================================================
# Invoice Schemas
# ============================================================================

class InvoiceLineItemCreate(BaseModel):
    """Create invoice line item"""
    description: str
    line_type: str  # subscription, usage, adjustment
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class InvoiceCreate(BaseModel):
    """Create invoice"""
    customer_id: UUID
    subscription_id: Optional[UUID] = None
    due_date: date
    line_items: List[InvoiceLineItemCreate]
    memo: Optional[str] = None
    auto_finalize: bool = True


class InvoiceLineItemResponse(BaseModel):
    """Invoice line item response"""
    id: UUID
    description: str
    line_type: str
    quantity: float
    unit_price: float
    amount: float
    discount_amount: float
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    is_proration: bool


class InvoiceResponse(BaseModel):
    """Invoice response"""
    id: UUID
    subscription_id: Optional[UUID]
    customer_id: UUID
    invoice_number: str
    status: str
    billing_period_start: Optional[datetime]
    billing_period_end: Optional[datetime]
    issue_date: Optional[datetime]
    due_date: Optional[datetime]
    subtotal: float
    tax_amount: float
    total_amount: float
    amount_paid: Optional[float]
    amount_due: Optional[float]
    currency: str
    pdf_url: Optional[str]
    paid_at: Optional[datetime]
    line_items: Optional[List[InvoiceLineItemResponse]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """List of invoices"""
    items: List[InvoiceResponse]
    total: int
    skip: int
    limit: int


class InvoiceSummary(BaseModel):
    """Invoice summary for dashboard"""
    total_outstanding: float
    total_overdue: float
    invoices_pending: int
    invoices_overdue: int


# ============================================================================
# Usage Schemas
# ============================================================================

class UsageRecordCreate(BaseModel):
    """Record usage event"""
    metric_type: UsageMetricTypeSchema
    quantity: Decimal
    user_id: Optional[UUID] = None
    resource_id: Optional[str] = None
    recorded_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class UsageRecordBatch(BaseModel):
    """Batch of usage records"""
    records: List[UsageRecordCreate]
    source: Optional[str] = None


class UsageRecordResponse(BaseModel):
    """Usage record response"""
    id: UUID
    metric_type: str
    quantity: float
    user_id: Optional[UUID]
    resource_id: Optional[str]
    recorded_at: datetime
    is_billable: bool
    billed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """Usage summary for a metric"""
    metric_type: str
    period_start: datetime
    period_end: datetime
    total_quantity: float
    included_quantity: float
    overage_quantity: float
    overage_amount: float
    unit: Optional[str]


class UsageDashboard(BaseModel):
    """Usage dashboard data"""
    period_start: datetime
    period_end: datetime
    summaries: List[UsageSummary]
    total_overage_amount: float
    usage_percentage: Dict[str, float]  # percentage of included used


class UsageAlert(BaseModel):
    """Usage threshold alert"""
    metric_type: str
    threshold_percent: int  # 80, 90, 100
    current_usage: float
    included_limit: float
    usage_percent: float
    alert_message: str


# ============================================================================
# Dunning Schemas
# ============================================================================

class DunningCampaignCreate(BaseModel):
    """Create dunning campaign"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    schedule: Optional[List[Dict[str, Any]]] = None
    email_templates: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None


class DunningCampaignResponse(BaseModel):
    """Dunning campaign response"""
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    schedule: List[Dict[str, Any]]
    email_templates: Dict[str, Any]
    retry_config: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DunningActionResponse(BaseModel):
    """Dunning action result"""
    action: str
    success: bool
    days_overdue: int
    details: Optional[Dict[str, Any]] = None


class DunningStatusResponse(BaseModel):
    """Dunning status for subscription"""
    has_active_dunning: bool
    campaigns: List[DunningCampaignResponse]
    total_outstanding: float


# ============================================================================
# Coupon Schemas
# ============================================================================

class CouponCreate(BaseModel):
    """Create coupon"""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    coupon_type: CouponTypeSchema
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    trial_extension_days: Optional[int] = None
    free_months: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_redemptions: Optional[int] = None
    max_redemptions_per_customer: int = 1
    applicable_plans: Optional[List[UUID]] = None
    min_subscription_amount: Optional[Decimal] = None
    first_time_only: bool = False
    duration: str = "once"  # once, repeating, forever
    duration_months: Optional[int] = None


class CouponResponse(BaseModel):
    """Coupon response"""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    coupon_type: str
    discount_percent: Optional[float]
    discount_amount: Optional[float]
    trial_extension_days: Optional[int]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    max_redemptions: Optional[int]
    redemption_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CouponValidation(BaseModel):
    """Coupon validation result"""
    is_valid: bool
    coupon: Optional[CouponResponse]
    discount_preview: Optional[float]
    error_message: Optional[str]


# ============================================================================
# Credit Memo Schemas
# ============================================================================

class CreditMemoCreate(BaseModel):
    """Create credit memo"""
    customer_id: UUID
    original_invoice_id: Optional[UUID] = None
    amount: Decimal
    reason: str
    description: Optional[str] = None


class CreditMemoResponse(BaseModel):
    """Credit memo response"""
    id: UUID
    customer_id: UUID
    original_invoice_id: Optional[UUID]
    applied_to_invoice_id: Optional[UUID] = None
    credit_number: str
    amount: float
    reason: str
    status: str
    applied_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Revenue Recognition Schemas
# ============================================================================

class RevenueRecognitionResponse(BaseModel):
    """Revenue recognition entry response"""
    id: UUID
    schedule_id: UUID
    period_start: datetime
    period_end: datetime
    amount: Decimal
    status: str
    recognized_at: Optional[datetime]

    class Config:
        from_attributes = True


class RevenueScheduleResponse(BaseModel):
    """Revenue schedule response"""
    id: UUID
    invoice_id: UUID
    subscription_id: Optional[UUID]
    total_amount: Decimal
    recognized_amount: Decimal
    deferred_amount: Decimal
    recognition_start: datetime
    recognition_end: datetime
    recognition_method: str
    status: str
    entries: Optional[List[RevenueRecognitionResponse]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RevenueRecognitionEntry(BaseModel):
    """Revenue recognition entry"""
    period_date: date
    amount: float
    journal_entry_id: Optional[str]
    exported_at: Optional[datetime]


class RevenueReport(BaseModel):
    """Revenue report"""
    period_start: date
    period_end: date
    recognized_revenue: float
    deferred_revenue: float
    by_month: Dict[str, float]


# ============================================================================
# Entitlement Schemas
# ============================================================================

class EntitlementResponse(BaseModel):
    """Entitlement response"""
    feature_key: str
    feature_name: str
    limit_type: str
    limit_value: Optional[int]
    current_usage: int
    is_enabled: bool
    is_override: bool
    usage_percentage: Optional[float]

    class Config:
        from_attributes = True


class EntitlementCheckResult(BaseModel):
    """Entitlement check result"""
    feature_key: str
    is_allowed: bool
    limit_value: Optional[int]
    current_usage: int
    remaining: Optional[int]
    message: Optional[str]


class EntitlementOverride(BaseModel):
    """Override entitlement"""
    feature_key: str
    limit_value: Optional[int] = None
    is_enabled: bool = True
    expires_at: Optional[datetime] = None


# ============================================================================
# Billing Portal Schemas
# ============================================================================

class BillingOverview(BaseModel):
    """Billing overview for portal"""
    subscription: Optional[SubscriptionResponse]
    current_plan: Optional[PlanResponse]
    next_invoice: Optional[InvoiceResponse]
    payment_method: Optional[PaymentMethodResponse]
    current_period_usage: UsageDashboard
    outstanding_balance: float
    credit_balance: float


class BillingHistory(BaseModel):
    """Billing history"""
    invoices: List[InvoiceResponse]
    payments: List[PaymentResponse]
    total_invoices: int
    total_payments: int


# ============================================================================
# SaaS Metrics Schemas
# ============================================================================

class MRRBreakdown(BaseModel):
    """MRR breakdown with changes"""
    current_mrr: float
    arr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churned_mrr: float
    reactivation_mrr: float
    net_mrr_change: float
    mrr_growth_rate: float
    as_of_date: str


class SaaSMetrics(BaseModel):
    """SaaS metrics dashboard"""
    mrr: float
    arr: float
    mrr_growth: float
    customer_count: int
    new_customers: int
    churned_customers: int
    net_revenue_retention: float
    gross_revenue_retention: float
    arpu: float  # Average revenue per user
    ltv: float   # Lifetime value


class SaaSMetricsResponse(BaseModel):
    """Comprehensive SaaS metrics response"""
    period: str
    period_start: str
    period_end: str
    mrr: float
    arr: float
    mrr_growth_rate: float
    active_subscriptions: int
    total_customers: int
    arpu: float
    customer_churn_rate: float
    revenue_churn_rate: float
    net_revenue_retention: float
    ltv: float
    ltv_cac_ratio: float
    period_revenue: float
    deferred_revenue: float
    mrr_breakdown: Dict[str, float]


class ChurnAnalysis(BaseModel):
    """Churn analysis"""
    period_start: str
    period_end: str
    subscriptions_at_start: int
    churned_subscriptions: int
    customer_churn_rate: float
    revenue_churn_rate: float
    churned_mrr: float
    mrr_at_start: float
    churn_reasons: Dict[str, int]
    net_revenue_retention: float


class CohortAnalysis(BaseModel):
    """Cohort retention analysis"""
    cohort_month: str
    customers_at_start: int
    retention_by_month: Dict[str, float]
    revenue_by_month: Dict[str, float]
