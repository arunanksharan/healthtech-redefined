"""EPIC-017: Revenue Infrastructure

Revision ID: 017_revenue_infrastructure
Revises: 016_mobile_applications
Create Date: 2024-11-25

This migration creates tables for:
- Subscription management
- Payment processing
- Invoice generation
- Usage metering
- Dunning/collections
- Revenue recognition
- Entitlements
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '017_revenue_infrastructure'
down_revision = '016_mobile_applications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    plan_type = postgresql.ENUM(
        'starter', 'professional', 'enterprise', 'custom',
        name='plan_type', create_type=False
    )
    billing_cycle = postgresql.ENUM(
        'monthly', 'annual', 'quarterly',
        name='billing_cycle', create_type=False
    )
    subscription_status = postgresql.ENUM(
        'trialing', 'active', 'past_due', 'suspended', 'canceled', 'expired',
        name='subscription_status', create_type=False
    )
    payment_method_type = postgresql.ENUM(
        'card', 'ach', 'wire', 'check',
        name='payment_method_type', create_type=False
    )
    payment_status = postgresql.ENUM(
        'pending', 'processing', 'succeeded', 'failed', 'refunded',
        'partially_refunded', 'canceled', 'disputed',
        name='payment_status', create_type=False
    )
    invoice_status = postgresql.ENUM(
        'draft', 'open', 'paid', 'past_due', 'void', 'uncollectible',
        name='invoice_status', create_type=False
    )
    usage_metric_type = postgresql.ENUM(
        'ai_interaction', 'ai_tokens', 'triage_agent', 'scribe_agent', 'coding_agent',
        'api_call', 'fhir_api', 'telehealth_minutes', 'sms_message', 'voice_minute',
        'whatsapp_message', 'email_send', 'storage_gb', 'document_processed',
        'active_patient', 'active_provider',
        name='usage_metric_type', create_type=False
    )
    dunning_status = postgresql.ENUM(
        'active', 'paused', 'recovered', 'failed', 'canceled',
        name='dunning_status', create_type=False
    )
    coupon_type = postgresql.ENUM(
        'percentage', 'fixed_amount', 'trial_extension', 'free_months',
        name='coupon_type', create_type=False
    )
    credit_memo_reason = postgresql.ENUM(
        'service_issue', 'billing_error', 'customer_goodwill', 'promotion',
        'downgrade_proration', 'cancellation',
        name='credit_memo_reason', create_type=False
    )

    # Create enums in database
    op.execute("CREATE TYPE plan_type AS ENUM ('starter', 'professional', 'enterprise', 'custom')")
    op.execute("CREATE TYPE billing_cycle AS ENUM ('monthly', 'annual', 'quarterly')")
    op.execute("CREATE TYPE subscription_status AS ENUM ('trialing', 'active', 'past_due', 'suspended', 'canceled', 'expired')")
    op.execute("CREATE TYPE payment_method_type AS ENUM ('card', 'ach', 'wire', 'check')")
    op.execute("CREATE TYPE payment_status AS ENUM ('pending', 'processing', 'succeeded', 'failed', 'refunded', 'partially_refunded', 'canceled', 'disputed')")
    op.execute("CREATE TYPE invoice_status AS ENUM ('draft', 'open', 'paid', 'past_due', 'void', 'uncollectible')")
    op.execute("CREATE TYPE usage_metric_type AS ENUM ('ai_interaction', 'ai_tokens', 'triage_agent', 'scribe_agent', 'coding_agent', 'api_call', 'fhir_api', 'telehealth_minutes', 'sms_message', 'voice_minute', 'whatsapp_message', 'email_send', 'storage_gb', 'document_processed', 'active_patient', 'active_provider')")
    op.execute("CREATE TYPE dunning_status AS ENUM ('active', 'paused', 'recovered', 'failed', 'canceled')")
    op.execute("CREATE TYPE coupon_type AS ENUM ('percentage', 'fixed_amount', 'trial_extension', 'free_months')")
    op.execute("CREATE TYPE credit_memo_reason AS ENUM ('service_issue', 'billing_error', 'customer_goodwill', 'promotion', 'downgrade_proration', 'cancellation')")

    # Plans table
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('plan_type', plan_type, nullable=False),
        sa.Column('monthly_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('annual_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('quarterly_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('features', postgresql.JSONB, server_default='{}'),
        sa.Column('limits', postgresql.JSONB, server_default='{}'),
        sa.Column('overage_rates', postgresql.JSONB, server_default='{}'),
        sa.Column('trial_days', sa.Integer, server_default='14'),
        sa.Column('trial_enabled', sa.Boolean, server_default='true'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_public', sa.Boolean, server_default='true'),
        sa.Column('is_legacy', sa.Boolean, server_default='false'),
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('stripe_product_id', sa.String(100), nullable=True),
        sa.Column('stripe_price_id_monthly', sa.String(100), nullable=True),
        sa.Column('stripe_price_id_annual', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_plans_slug', 'plans', ['slug'])
    op.create_index('idx_plans_type', 'plans', ['plan_type'])
    op.create_index('idx_plans_active', 'plans', ['is_active'])

    # Billing customers table
    op.create_table(
        'billing_customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('billing_address_line1', sa.String(255), nullable=True),
        sa.Column('billing_address_line2', sa.String(255), nullable=True),
        sa.Column('billing_city', sa.String(100), nullable=True),
        sa.Column('billing_state', sa.String(100), nullable=True),
        sa.Column('billing_postal_code', sa.String(20), nullable=True),
        sa.Column('billing_country', sa.String(2), server_default='US'),
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('tax_exempt', sa.Boolean, server_default='false'),
        sa.Column('tax_exempt_certificate', sa.String(255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True, unique=True),
        sa.Column('default_payment_method_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_settings', postgresql.JSONB, server_default='{}'),
        sa.Column('payment_terms_days', sa.Integer, server_default='0'),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('credit_balance', sa.Numeric(10, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_billing_customers_tenant', 'billing_customers', ['tenant_id'])
    op.create_index('idx_billing_customers_stripe', 'billing_customers', ['stripe_customer_id'])

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('status', subscription_status, server_default='trialing'),
        sa.Column('billing_cycle', billing_cycle, server_default='monthly'),
        sa.Column('quantity', sa.Integer, server_default='1'),
        sa.Column('provider_count', sa.Integer, server_default='1'),
        sa.Column('facility_count', sa.Integer, server_default='1'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean, server_default='false'),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), server_default='0'),
        sa.Column('mrr', sa.Numeric(10, 2), nullable=True),
        sa.Column('arr', sa.Numeric(12, 2), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('cancellation_reason', sa.Text, nullable=True),
        sa.Column('cancellation_feedback', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_subscriptions_tenant', 'subscriptions', ['tenant_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_subscriptions_stripe', 'subscriptions', ['stripe_subscription_id'])

    # Subscription changes table
    op.create_table(
        'subscription_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('from_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id'), nullable=True),
        sa.Column('to_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id'), nullable=True),
        sa.Column('from_quantity', sa.Integer, nullable=True),
        sa.Column('to_quantity', sa.Integer, nullable=True),
        sa.Column('proration_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('proration_credit', sa.Numeric(10, 2), server_default='0'),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_subscription_changes_sub', 'subscription_changes', ['subscription_id'])

    # Payment methods table
    op.create_table(
        'payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_customers.id'), nullable=False),
        sa.Column('method_type', payment_method_type, nullable=False),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('card_brand', sa.String(20), nullable=True),
        sa.Column('card_last4', sa.String(4), nullable=True),
        sa.Column('card_exp_month', sa.Integer, nullable=True),
        sa.Column('card_exp_year', sa.Integer, nullable=True),
        sa.Column('card_funding', sa.String(20), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_last4', sa.String(4), nullable=True),
        sa.Column('bank_routing_last4', sa.String(4), nullable=True),
        sa.Column('bank_account_type', sa.String(20), nullable=True),
        sa.Column('stripe_payment_method_id', sa.String(100), nullable=True, unique=True),
        sa.Column('is_verified', sa.Boolean, server_default='false'),
        sa.Column('verification_status', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_payment_methods_customer', 'payment_methods', ['customer_id'])
    op.create_index('idx_payment_methods_stripe', 'payment_methods', ['stripe_payment_method_id'])

    # Invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_customers.id'), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=False, unique=True),
        sa.Column('status', invoice_status, server_default='draft'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('tax_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('amount_paid', sa.Numeric(10, 2), server_default='0'),
        sa.Column('amount_due', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('tax_rate', sa.Numeric(5, 4), server_default='0'),
        sa.Column('tax_jurisdiction', sa.String(100), nullable=True),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(100), nullable=True, unique=True),
        sa.Column('memo', sa.Text, nullable=True),
        sa.Column('footer', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_invoices_tenant', 'invoices', ['tenant_id'])
    op.create_index('idx_invoices_customer', 'invoices', ['customer_id'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])
    op.create_index('idx_invoices_due_date', 'invoices', ['due_date'])
    op.create_index('idx_invoices_stripe', 'invoices', ['stripe_invoice_id'])

    # Invoice line items table
    op.create_table(
        'invoice_line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('line_type', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 4), server_default='1'),
        sa.Column('unit_price', sa.Numeric(10, 4), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id'), nullable=True),
        sa.Column('usage_metric_type', usage_metric_type, nullable=True),
        sa.Column('is_proration', sa.Boolean, server_default='false'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_invoice_line_items_invoice', 'invoice_line_items', ['invoice_id'])

    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_customers.id'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_methods.id'), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('amount_refunded', sa.Numeric(10, 2), server_default='0'),
        sa.Column('status', payment_status, server_default='pending'),
        sa.Column('failure_reason', sa.Text, nullable=True),
        sa.Column('failure_code', sa.String(50), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True, unique=True),
        sa.Column('stripe_charge_id', sa.String(100), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('receipt_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_payments_customer', 'payments', ['customer_id'])
    op.create_index('idx_payments_invoice', 'payments', ['invoice_id'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_payments_stripe', 'payments', ['stripe_payment_intent_id'])

    # Credit memos table
    op.create_table(
        'credit_memos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_customers.id'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=True),
        sa.Column('credit_memo_number', sa.String(50), nullable=False, unique=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('amount_remaining', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', credit_memo_reason, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_voided', sa.Boolean, server_default='false'),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('applied_to_invoices', postgresql.JSONB, server_default='[]'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_credit_memos_tenant', 'credit_memos', ['tenant_id'])
    op.create_index('idx_credit_memos_customer', 'credit_memos', ['customer_id'])

    # Usage records table
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('metric_type', usage_metric_type, nullable=False),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_billable', sa.Boolean, server_default='true'),
        sa.Column('billed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invoice_line_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_usage_records_tenant_metric', 'usage_records', ['tenant_id', 'metric_type'])
    op.create_index('idx_usage_records_recorded', 'usage_records', ['recorded_at'])
    op.create_index('idx_usage_records_billable', 'usage_records', ['is_billable', 'billed_at'])

    # Usage aggregates table
    op.create_table(
        'usage_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_type', usage_metric_type, nullable=False),
        sa.Column('total_quantity', sa.Numeric(14, 4), nullable=False),
        sa.Column('record_count', sa.Integer, nullable=False),
        sa.Column('included_quantity', sa.Numeric(14, 4), server_default='0'),
        sa.Column('overage_quantity', sa.Numeric(14, 4), server_default='0'),
        sa.Column('overage_rate', sa.Numeric(10, 4), server_default='0'),
        sa.Column('overage_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_usage_aggregates_tenant_period', 'usage_aggregates', ['tenant_id', 'period_start', 'period_end'])
    op.create_index('idx_usage_aggregates_metric', 'usage_aggregates', ['metric_type', 'period_start'])
    op.create_unique_constraint('uq_usage_aggregates_period', 'usage_aggregates', ['tenant_id', 'metric_type', 'period_type', 'period_start'])

    # Dunning campaigns table
    op.create_table(
        'dunning_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('status', dunning_status, server_default='active'),
        sa.Column('failed_payment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('failure_reason', sa.Text, nullable=True),
        sa.Column('original_failure_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='4'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notifications_sent', sa.Integer, server_default='0'),
        sa.Column('last_notification_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_history', postgresql.JSONB, server_default='[]'),
        sa.Column('grace_period_ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_in_grace_period', sa.Boolean, server_default='true'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_type', sa.String(50), nullable=True),
        sa.Column('successful_payment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_dunning_campaigns_tenant', 'dunning_campaigns', ['tenant_id'])
    op.create_index('idx_dunning_campaigns_status', 'dunning_campaigns', ['status'])
    op.create_index('idx_dunning_campaigns_next_retry', 'dunning_campaigns', ['next_retry_at'])

    # Coupons table
    op.create_table(
        'coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('coupon_type', coupon_type, nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('trial_extension_days', sa.Integer, nullable=True),
        sa.Column('free_months', sa.Integer, nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_redemptions', sa.Integer, nullable=True),
        sa.Column('redemption_count', sa.Integer, server_default='0'),
        sa.Column('max_redemptions_per_customer', sa.Integer, server_default='1'),
        sa.Column('applicable_plans', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('min_subscription_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('first_time_only', sa.Boolean, server_default='false'),
        sa.Column('duration', sa.String(20), server_default='once'),
        sa.Column('duration_months', sa.Integer, nullable=True),
        sa.Column('stripe_coupon_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_coupons_code', 'coupons', ['code'])
    op.create_index('idx_coupons_active', 'coupons', ['is_active'])

    # Coupon redemptions table
    op.create_table(
        'coupon_redemptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('coupon_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('coupons.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('remaining_applications', sa.Integer, nullable=True),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_coupon_redemptions_tenant', 'coupon_redemptions', ['tenant_id'])
    op.create_index('idx_coupon_redemptions_coupon', 'coupon_redemptions', ['coupon_id'])

    # Revenue schedules table
    op.create_table(
        'revenue_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('invoice_line_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoice_line_items.id'), nullable=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('recognized_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('deferred_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('recognition_start', sa.Date, nullable=False),
        sa.Column('recognition_end', sa.Date, nullable=False),
        sa.Column('recognition_method', sa.String(50), server_default='straight_line'),
        sa.Column('is_complete', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_revenue_schedules_tenant', 'revenue_schedules', ['tenant_id'])
    op.create_index('idx_revenue_schedules_period', 'revenue_schedules', ['recognition_start', 'recognition_end'])

    # Revenue recognitions table
    op.create_table(
        'revenue_recognitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('revenue_schedules.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_date', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('journal_entry_id', sa.String(100), nullable=True),
        sa.Column('exported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_revenue_recognitions_schedule', 'revenue_recognitions', ['schedule_id'])
    op.create_index('idx_revenue_recognitions_period', 'revenue_recognitions', ['period_date'])

    # Entitlements table
    op.create_table(
        'entitlements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=False),
        sa.Column('feature_key', sa.String(100), nullable=False),
        sa.Column('feature_name', sa.String(200), nullable=False),
        sa.Column('limit_type', sa.String(20), nullable=False),
        sa.Column('limit_value', sa.Integer, nullable=True),
        sa.Column('current_usage', sa.Integer, server_default='0'),
        sa.Column('is_enabled', sa.Boolean, server_default='true'),
        sa.Column('is_override', sa.Boolean, server_default='false'),
        sa.Column('override_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_entitlements_tenant', 'entitlements', ['tenant_id'])
    op.create_index('idx_entitlements_feature', 'entitlements', ['feature_key'])
    op.create_unique_constraint('uq_entitlements_sub_feature', 'entitlements', ['subscription_id', 'feature_key'])

    # Billing audit logs table
    op.create_table(
        'billing_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('action_category', sa.String(50), nullable=False),
        sa.Column('action_description', sa.Text, nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_billing_audit_tenant', 'billing_audit_logs', ['tenant_id'])
    op.create_index('idx_billing_audit_action', 'billing_audit_logs', ['action'])
    op.create_index('idx_billing_audit_resource', 'billing_audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_billing_audit_created', 'billing_audit_logs', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('billing_audit_logs')
    op.drop_table('entitlements')
    op.drop_table('revenue_recognitions')
    op.drop_table('revenue_schedules')
    op.drop_table('coupon_redemptions')
    op.drop_table('coupons')
    op.drop_table('dunning_campaigns')
    op.drop_table('usage_aggregates')
    op.drop_table('usage_records')
    op.drop_table('credit_memos')
    op.drop_table('payments')
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
    op.drop_table('payment_methods')
    op.drop_table('subscription_changes')
    op.drop_table('subscriptions')
    op.drop_table('billing_customers')
    op.drop_table('plans')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS credit_memo_reason")
    op.execute("DROP TYPE IF EXISTS coupon_type")
    op.execute("DROP TYPE IF EXISTS dunning_status")
    op.execute("DROP TYPE IF EXISTS usage_metric_type")
    op.execute("DROP TYPE IF EXISTS invoice_status")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.execute("DROP TYPE IF EXISTS payment_method_type")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS billing_cycle")
    op.execute("DROP TYPE IF EXISTS plan_type")
