"""
Revenue Infrastructure Router
EPIC-017: FastAPI endpoints for billing and revenue
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from modules.revenue.services import (
    SubscriptionService,
    UsageMeteringService,
    PaymentService,
    InvoiceService,
    DunningService,
    RevenueService
)
from modules.revenue.schemas import (
    # Plan schemas
    PlanCreate, PlanUpdate, PlanResponse, PlanListResponse, PlanComparisonResponse,
    # Subscription schemas
    SubscriptionCreate, SubscriptionUpdate, SubscriptionChangePlan,
    SubscriptionCancel, SubscriptionResponse, SubscriptionListResponse, ProrationPreview,
    # Customer schemas
    CustomerCreate, CustomerUpdate, CustomerResponse,
    # Payment method schemas
    PaymentMethodCreate, PaymentMethodResponse, PaymentMethodListResponse,
    # Payment schemas
    PaymentCreate, PaymentRefund, PaymentResponse, PaymentListResponse,
    # Usage schemas
    UsageRecordCreate, UsageRecordBatch, UsageRecordResponse,
    UsageSummary, UsageDashboard, UsageAlert,
    # Invoice schemas
    InvoiceCreate, InvoiceResponse, InvoiceListResponse, InvoiceSummary,
    CreditMemoCreate, CreditMemoResponse,
    # Dunning schemas
    DunningCampaignCreate, DunningCampaignResponse,
    # Revenue schemas
    RevenueScheduleResponse, RevenueRecognitionResponse,
    SaaSMetricsResponse, MRRBreakdown, ChurnAnalysis,
    # Coupon schemas
    CouponCreate, CouponResponse, CouponValidation,
    # Entitlement schemas
    EntitlementResponse, EntitlementCheckResult, EntitlementOverride,
    # Billing portal schemas
    BillingOverview, BillingHistory,
    # SaaS metrics schemas
    SaaSMetrics,
    # Enums
    SubscriptionStatusSchema, PaymentStatusSchema, UsageMetricTypeSchema
)
from modules.revenue.models import (
    SubscriptionStatus, PaymentStatus, UsageMetricType
)


router = APIRouter(prefix="/revenue", tags=["Revenue Infrastructure"])

# Service instances
subscription_service = SubscriptionService()
usage_service = UsageMeteringService()
payment_service = PaymentService()
invoice_service = InvoiceService()
dunning_service = DunningService()
revenue_service = RevenueService()


# ============================================================================
# Plan Management Endpoints
# ============================================================================

@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    active_only: bool = Query(True),
    public_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """List available subscription plans"""
    from modules.revenue.models import Plan
    from sqlalchemy import select, and_

    query = select(Plan)
    if active_only:
        query = query.where(Plan.is_active == True)
    if public_only:
        query = query.where(Plan.is_public == True)

    query = query.order_by(Plan.sort_order)
    result = await db.execute(query)
    plans = result.scalars().all()

    return PlanListResponse(
        plans=[PlanResponse(
            id=p.id, name=p.name, slug=p.slug, description=p.description,
            plan_type=p.plan_type.value, monthly_price=float(p.monthly_price) if p.monthly_price else None,
            annual_price=float(p.annual_price) if p.annual_price else None,
            quarterly_price=float(p.quarterly_price) if p.quarterly_price else None,
            currency=p.currency, features=p.features or {}, limits=p.limits or {},
            overage_rates=p.overage_rates or {}, trial_days=p.trial_days,
            trial_enabled=p.trial_enabled, is_active=p.is_active, is_public=p.is_public,
            is_legacy=p.is_legacy, created_at=p.created_at
        ) for p in plans],
        total=len(plans)
    )


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get plan by ID"""
    from modules.revenue.models import Plan
    from sqlalchemy import select

    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return PlanResponse(
        id=plan.id, name=plan.name, slug=plan.slug, description=plan.description,
        plan_type=plan.plan_type.value, monthly_price=float(plan.monthly_price) if plan.monthly_price else None,
        annual_price=float(plan.annual_price) if plan.annual_price else None,
        quarterly_price=float(plan.quarterly_price) if plan.quarterly_price else None,
        currency=plan.currency, features=plan.features or {}, limits=plan.limits or {},
        overage_rates=plan.overage_rates or {}, trial_days=plan.trial_days,
        trial_enabled=plan.trial_enabled, is_active=plan.is_active, is_public=plan.is_public,
        is_legacy=plan.is_legacy, created_at=plan.created_at
    )


# ============================================================================
# Subscription Endpoints
# ============================================================================

@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    data: SubscriptionCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new subscription"""
    try:
        return await subscription_service.create_subscription(db, tenant_id, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get current active subscription for tenant"""
    subscription = await subscription_service.get_tenant_subscription(db, tenant_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return subscription


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get subscription by ID"""
    try:
        return await subscription_service.get_subscription(db, subscription_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    data: SubscriptionUpdate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update subscription quantity/metadata"""
    try:
        return await subscription_service.update_quantity(
            db, subscription_id, tenant_id, data, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/{subscription_id}/change-plan", response_model=SubscriptionResponse)
async def change_subscription_plan(
    subscription_id: UUID,
    data: SubscriptionChangePlan,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Change subscription plan (upgrade/downgrade)"""
    try:
        return await subscription_service.change_plan(
            db, subscription_id, tenant_id, data, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/{subscription_id}/proration-preview", response_model=ProrationPreview)
async def preview_proration(
    subscription_id: UUID,
    new_plan_id: UUID = Query(...),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Preview proration for plan change"""
    try:
        subscription = await subscription_service.get_subscription(db, subscription_id, tenant_id)
        from modules.revenue.models import Plan, Subscription
        from sqlalchemy import select

        # Get plans
        current_plan_result = await db.execute(select(Plan).where(Plan.id == subscription.plan_id))
        current_plan = current_plan_result.scalar_one()

        new_plan_result = await db.execute(select(Plan).where(Plan.id == new_plan_id))
        new_plan = new_plan_result.scalar_one_or_none()

        if not new_plan:
            raise HTTPException(status_code=404, detail="New plan not found")

        sub_result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
        sub = sub_result.scalar_one()

        return await subscription_service.calculate_proration(db, sub, current_plan, new_plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: UUID,
    data: SubscriptionCancel,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Cancel subscription"""
    try:
        return await subscription_service.cancel_subscription(
            db, subscription_id, tenant_id, data, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/{subscription_id}/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    subscription_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Reactivate a canceled subscription"""
    try:
        return await subscription_service.reactivate_subscription(
            db, subscription_id, tenant_id, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Customer Endpoints
# ============================================================================

@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create billing customer"""
    try:
        return await payment_service.create_customer(db, tenant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customers", response_model=CustomerResponse)
async def get_customer(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get billing customer"""
    try:
        return await payment_service.get_customer(db, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/customers", response_model=CustomerResponse)
async def update_customer(
    data: CustomerUpdate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Update billing customer"""
    try:
        return await payment_service.update_customer(db, tenant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Payment Method Endpoints
# ============================================================================

@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    data: PaymentMethodCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Add payment method"""
    try:
        return await payment_service.add_payment_method(db, tenant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-methods", response_model=PaymentMethodListResponse)
async def list_payment_methods(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """List payment methods"""
    return await payment_service.list_payment_methods(db, tenant_id)


@router.delete("/payment-methods/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Remove payment method"""
    try:
        await payment_service.remove_payment_method(db, tenant_id, payment_method_id)
        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-methods/{payment_method_id}/set-default")
async def set_default_payment_method(
    payment_method_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Set default payment method"""
    try:
        await payment_service.set_default_payment_method(db, tenant_id, payment_method_id)
        return {"status": "default_set"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Payment Endpoints
# ============================================================================

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    data: PaymentCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a payment"""
    try:
        return await payment_service.create_payment(db, tenant_id, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    status: Optional[PaymentStatusSchema] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """List payments"""
    status_enum = PaymentStatus(status.value) if status else None
    return await payment_service.list_payments(db, tenant_id, status_enum, limit, offset)


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get payment by ID"""
    try:
        return await payment_service.get_payment(db, tenant_id, payment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: UUID,
    data: PaymentRefund,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Refund a payment"""
    try:
        return await payment_service.refund_payment(db, tenant_id, payment_id, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Usage Metering Endpoints
# ============================================================================

@router.post("/usage", response_model=UsageRecordResponse)
async def record_usage(
    data: UsageRecordCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Record a usage event"""
    return await usage_service.record_usage(db, tenant_id, data)


@router.post("/usage/batch", response_model=List[UsageRecordResponse])
async def record_usage_batch(
    data: UsageRecordBatch,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Record multiple usage events"""
    return await usage_service.record_usage_batch(db, tenant_id, data)


@router.get("/usage/summary", response_model=UsageSummary)
async def get_usage_summary(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_type: UsageMetricTypeSchema = Query(...),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get usage summary for a metric"""
    return await usage_service.get_usage_summary(
        db, tenant_id, UsageMetricType(metric_type.value), period_start, period_end
    )


@router.get("/usage/dashboard", response_model=UsageDashboard)
async def get_usage_dashboard(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    period_start: Optional[datetime] = Query(None),
    period_end: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get usage dashboard"""
    return await usage_service.get_usage_dashboard(db, tenant_id, period_start, period_end)


@router.get("/usage/alerts", response_model=List[UsageAlert])
async def get_usage_alerts(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get usage threshold alerts"""
    return await usage_service.check_usage_alerts(db, tenant_id)


@router.get("/usage/forecast")
async def get_usage_forecast(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_type: UsageMetricTypeSchema = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get usage forecast"""
    return await usage_service.forecast_usage(
        db, tenant_id, UsageMetricType(metric_type.value)
    )


# ============================================================================
# Webhook Endpoint
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhooks"""
    # In production, verify Stripe signature
    body = await request.json()
    event_type = body.get("type")
    event_data = body.get("data", {}).get("object", {})

    await payment_service.handle_webhook(db, event_type, event_data)
    return {"received": True}


# ============================================================================
# Billing Portal Endpoints
# ============================================================================

@router.get("/billing/overview", response_model=BillingOverview)
async def get_billing_overview(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get billing overview for portal"""
    subscription = await subscription_service.get_tenant_subscription(db, tenant_id)

    try:
        customer = await payment_service.get_customer(db, tenant_id)
        payment_methods = await payment_service.list_payment_methods(db, tenant_id)
        default_pm = None
        if payment_methods.default_id:
            for pm in payment_methods.payment_methods:
                if pm.id == payment_methods.default_id:
                    default_pm = pm
                    break
    except ValueError:
        customer = None
        default_pm = None

    usage_dashboard = await usage_service.get_usage_dashboard(db, tenant_id)

    # Get plan if subscription exists
    current_plan = None
    if subscription:
        from modules.revenue.models import Plan
        from sqlalchemy import select
        result = await db.execute(select(Plan).where(Plan.id == subscription.plan_id))
        plan = result.scalar_one_or_none()
        if plan:
            current_plan = PlanResponse(
                id=plan.id, name=plan.name, slug=plan.slug, description=plan.description,
                plan_type=plan.plan_type.value, monthly_price=float(plan.monthly_price) if plan.monthly_price else None,
                annual_price=float(plan.annual_price) if plan.annual_price else None,
                quarterly_price=float(plan.quarterly_price) if plan.quarterly_price else None,
                currency=plan.currency, features=plan.features or {}, limits=plan.limits or {},
                overage_rates=plan.overage_rates or {}, trial_days=plan.trial_days,
                trial_enabled=plan.trial_enabled, is_active=plan.is_active, is_public=plan.is_public,
                is_legacy=plan.is_legacy, created_at=plan.created_at
            )

    return BillingOverview(
        subscription=subscription,
        current_plan=current_plan,
        next_invoice=None,
        payment_method=default_pm,
        current_period_usage=usage_dashboard,
        outstanding_balance=0,
        credit_balance=float(customer.credit_balance) if customer else 0
    )


# ============================================================================
# Invoice Endpoints
# ============================================================================

@router.post("/invoices/generate", response_model=InvoiceResponse)
async def generate_invoice(
    subscription_id: UUID = Query(..., description="Subscription ID"),
    billing_period_start: datetime = Query(...),
    billing_period_end: datetime = Query(...),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Generate an invoice for a subscription billing period"""
    try:
        return await invoice_service.generate_invoice(
            db, tenant_id, subscription_id, billing_period_start, billing_period_end, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    customer_id: Optional[UUID] = Query(None),
    subscription_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List invoices with filters"""
    return await invoice_service.list_invoices(
        db, tenant_id, customer_id, subscription_id, status, skip, limit
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get invoice by ID"""
    try:
        return await invoice_service.get_invoice(db, tenant_id, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/invoices/{invoice_id}/finalize", response_model=InvoiceResponse)
async def finalize_invoice(
    invoice_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Finalize a draft invoice"""
    try:
        return await invoice_service.finalize_invoice(db, tenant_id, invoice_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    delivery_method: str = Query("email"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Send invoice to customer"""
    try:
        return await invoice_service.send_invoice(
            db, tenant_id, invoice_id, delivery_method, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: UUID,
    payment_id: UUID = Query(..., description="Payment ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Mark invoice as paid"""
    try:
        return await invoice_service.mark_as_paid(db, tenant_id, invoice_id, payment_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: UUID,
    reason: str = Query(..., description="Void reason"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Void an invoice"""
    try:
        return await invoice_service.void_invoice(db, tenant_id, invoice_id, reason, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices/overdue", response_model=List[InvoiceResponse])
async def get_overdue_invoices(
    tenant_id: Optional[UUID] = Query(None),
    days_overdue: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Get overdue invoices"""
    return await invoice_service.get_overdue_invoices(db, tenant_id, days_overdue)


# ============================================================================
# Credit Memo Endpoints
# ============================================================================

@router.post("/credit-memos", response_model=CreditMemoResponse)
async def create_credit_memo(
    data: CreditMemoCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a credit memo"""
    try:
        return await invoice_service.create_credit_memo(db, tenant_id, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/credit-memos/{credit_memo_id}/apply", response_model=CreditMemoResponse)
async def apply_credit_memo(
    credit_memo_id: UUID,
    invoice_id: UUID = Query(..., description="Invoice to apply credit to"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Apply credit memo to an invoice"""
    try:
        return await invoice_service.apply_credit_memo(
            db, tenant_id, credit_memo_id, invoice_id, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Dunning Endpoints
# ============================================================================

@router.post("/dunning/campaigns", response_model=DunningCampaignResponse)
async def create_dunning_campaign(
    data: DunningCampaignCreate,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a dunning campaign"""
    try:
        return await dunning_service.create_dunning_campaign(db, tenant_id, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dunning/campaigns", response_model=List[DunningCampaignResponse])
async def list_dunning_campaigns(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List dunning campaigns"""
    return await dunning_service.list_dunning_campaigns(db, tenant_id, active_only)


@router.get("/dunning/campaigns/{campaign_id}", response_model=DunningCampaignResponse)
async def get_dunning_campaign(
    campaign_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get dunning campaign by ID"""
    try:
        return await dunning_service.get_dunning_campaign(db, tenant_id, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/dunning/process")
async def process_dunning(
    tenant_id: Optional[UUID] = Query(None),
    batch_size: int = Query(100),
    db: AsyncSession = Depends(get_db)
):
    """Process dunning for overdue invoices (admin endpoint)"""
    return await dunning_service.process_dunning(db, tenant_id, batch_size)


@router.post("/dunning/recover/{subscription_id}")
async def recover_subscription(
    subscription_id: UUID,
    payment_id: UUID = Query(..., description="Payment ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Recover a suspended subscription after payment"""
    try:
        return await dunning_service.recover_subscription(
            db, tenant_id, subscription_id, payment_id, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dunning/statistics")
async def get_dunning_statistics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get dunning and collections statistics"""
    return await dunning_service.get_dunning_statistics(db, tenant_id, period_start, period_end)


# ============================================================================
# Revenue Recognition Endpoints
# ============================================================================

@router.post("/revenue/schedule", response_model=RevenueScheduleResponse)
async def create_revenue_schedule(
    invoice_id: UUID = Query(..., description="Invoice ID"),
    tenant_id: UUID = Query(..., description="Tenant ID"),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create revenue recognition schedule for an invoice"""
    try:
        return await revenue_service.create_revenue_schedule(db, tenant_id, invoice_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/revenue/process-recognition")
async def process_revenue_recognition(
    tenant_id: Optional[UUID] = Query(None),
    recognition_date: Optional[datetime] = Query(None),
    batch_size: int = Query(100),
    db: AsyncSession = Depends(get_db)
):
    """Process pending revenue recognition entries"""
    return await revenue_service.process_revenue_recognition(
        db, tenant_id, recognition_date, batch_size
    )


@router.get("/revenue/recognition-report")
async def get_revenue_recognition_report(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get ASC 606 compliant revenue recognition report"""
    return await revenue_service.get_revenue_recognition_report(
        db, tenant_id, period_start, period_end
    )


# ============================================================================
# SaaS Metrics Endpoints
# ============================================================================

@router.get("/metrics/mrr", response_model=MRRBreakdown)
async def get_mrr_breakdown(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    as_of_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get MRR breakdown with changes"""
    return await revenue_service.calculate_mrr(db, tenant_id, as_of_date)


@router.get("/metrics/churn", response_model=ChurnAnalysis)
async def get_churn_analysis(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get churn analysis"""
    return await revenue_service.calculate_churn(db, tenant_id, period_start, period_end)


@router.get("/metrics/ltv")
async def get_ltv(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    customer_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get customer lifetime value"""
    return await revenue_service.calculate_ltv(db, tenant_id, customer_id)


@router.get("/metrics/saas", response_model=SaaSMetricsResponse)
async def get_saas_metrics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    period: str = Query("month", description="Period: month, quarter, year"),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive SaaS metrics dashboard"""
    return await revenue_service.get_saas_metrics(db, tenant_id, period)
