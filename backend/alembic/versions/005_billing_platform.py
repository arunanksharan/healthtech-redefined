"""EPIC-008: Insurance & Billing Integration Database Tables

Revision ID: 005_billing_platform
Revises: 004_telehealth_platform
Create Date: 2024-01-25

This migration creates all tables for EPIC-008 Insurance & Billing Integration:
- Insurance Policies & Coverage (US-008.1)
- Eligibility Verification Records (US-008.1)
- Prior Authorization Management (US-008.2)
- Claims Generation & Submission (US-008.3)
- Payment Processing & Reconciliation (US-008.4)
- Patient Billing & Collections (US-008.5)
- Fee Schedule Management (US-008.6)
- Contract Management (US-008.7)
- Denial Management & Appeals (US-008.9)
- Billing Audit Logs (US-008.9)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '005_billing_platform'
down_revision = '004_telehealth_platform'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Insurance Policies ====================
    op.create_table(
        'insurance_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Payer information
        sa.Column('payer_id', sa.String(50), nullable=False),
        sa.Column('payer_name', sa.String(200), nullable=False),
        sa.Column('payer_address', sa.Text),
        sa.Column('payer_phone', sa.String(20)),
        sa.Column('payer_portal_url', sa.String(500)),
        # Plan details
        sa.Column('plan_name', sa.String(200)),
        sa.Column('plan_type', sa.String(50)),
        sa.Column('group_number', sa.String(50)),
        sa.Column('group_name', sa.String(200)),
        # Member info
        sa.Column('member_id', sa.String(50), nullable=False),
        sa.Column('subscriber_id', sa.String(50)),
        sa.Column('subscriber_name', sa.String(200)),
        sa.Column('relationship_to_subscriber', sa.String(20), default='self'),
        # Coverage period
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('termination_date', sa.Date),
        # Coverage details
        sa.Column('coverage_types', postgresql.ARRAY(sa.String(50)), default=[]),
        sa.Column('is_primary', sa.Boolean, default=True),
        sa.Column('coordination_order', sa.Integer, default=1),
        # Status
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
        sa.Column('verification_source', sa.String(50)),
        # Benefits summary
        sa.Column('benefits_summary', postgresql.JSONB, default={}),
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_insurance_policies_tenant', 'insurance_policies', ['tenant_id'])
    op.create_index('ix_insurance_policies_patient', 'insurance_policies', ['patient_id'])
    op.create_index('ix_insurance_policies_payer', 'insurance_policies', ['payer_id'])
    op.create_index('idx_insurance_policies_tenant_patient', 'insurance_policies', ['tenant_id', 'patient_id'])

    # ==================== Eligibility Verifications ====================
    op.create_table(
        'eligibility_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('insurance_policies.id')),
        # Request details
        sa.Column('payer_id', sa.String(50), nullable=False),
        sa.Column('member_id', sa.String(50), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('provider_npi', sa.String(10)),
        sa.Column('service_type', sa.String(50)),
        sa.Column('service_date', sa.Date),
        # Timing
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('responded_at', sa.DateTime(timezone=True)),
        sa.Column('response_time_ms', sa.Integer),
        # Response
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.Text),
        # Coverage results
        sa.Column('eligibility_status', sa.String(20)),
        sa.Column('coverage_active', sa.Boolean, default=False),
        sa.Column('coverage_details', postgresql.JSONB, default={}),
        # Service-specific results
        sa.Column('service_eligible', sa.Boolean, default=True),
        sa.Column('copay_amount', sa.Numeric(10, 2), default=0),
        sa.Column('coinsurance_percent', sa.Float, default=0),
        sa.Column('deductible_remaining', sa.Numeric(10, 2)),
        sa.Column('out_of_pocket_remaining', sa.Numeric(10, 2)),
        sa.Column('prior_auth_required', sa.Boolean, default=False),
        sa.Column('estimated_patient_responsibility', sa.Numeric(10, 2)),
        # Source tracking
        sa.Column('source', sa.String(50), default='api'),
        sa.Column('clearinghouse_id', sa.String(100)),
        sa.Column('trace_number', sa.String(50)),
        # Raw data
        sa.Column('raw_request', postgresql.JSONB),
        sa.Column('raw_response', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_eligibility_verifications_tenant', 'eligibility_verifications', ['tenant_id'])
    op.create_index('ix_eligibility_verifications_patient', 'eligibility_verifications', ['patient_id'])
    op.create_index('idx_eligibility_verifications_tenant_patient', 'eligibility_verifications', ['tenant_id', 'patient_id'])
    op.create_index('idx_eligibility_verifications_date', 'eligibility_verifications', ['requested_at'])

    # ==================== Prior Authorizations ====================
    op.create_table(
        'prior_authorizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('insurance_policies.id')),
        # Authorization details
        sa.Column('auth_number', sa.String(50)),
        sa.Column('payer_id', sa.String(50), nullable=False),
        sa.Column('payer_name', sa.String(200)),
        # Service details
        sa.Column('service_type', sa.String(100)),
        sa.Column('procedure_codes', postgresql.ARRAY(sa.String(20)), default=[]),
        sa.Column('diagnosis_codes', postgresql.ARRAY(sa.String(20)), default=[]),
        sa.Column('quantity_requested', sa.Integer, default=1),
        sa.Column('quantity_approved', sa.Integer),
        # Provider info
        sa.Column('requesting_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('requesting_provider_npi', sa.String(10)),
        sa.Column('performing_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('performing_provider_npi', sa.String(10)),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True)),
        sa.Column('facility_npi', sa.String(10)),
        # Clinical information
        sa.Column('clinical_summary', sa.Text),
        sa.Column('medical_necessity', sa.Text),
        # Dates
        sa.Column('requested_date', sa.Date),
        sa.Column('service_date_start', sa.Date),
        sa.Column('service_date_end', sa.Date),
        sa.Column('effective_date', sa.Date),
        sa.Column('expiration_date', sa.Date),
        # Status tracking
        sa.Column('status', sa.String(30), default='draft'),
        sa.Column('status_reason', sa.Text),
        # Submission
        sa.Column('submission_method', sa.String(30)),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True)),
        sa.Column('reference_number', sa.String(50)),
        # Response
        sa.Column('decision_date', sa.Date),
        sa.Column('decision_reason', sa.Text),
        sa.Column('payer_notes', sa.Text),
        # Appeal tracking
        sa.Column('appeal_deadline', sa.Date),
        sa.Column('appealed_at', sa.DateTime(timezone=True)),
        sa.Column('appeal_status', sa.String(30)),
        sa.Column('appeal_notes', sa.Text),
        # Documents
        sa.Column('documents', postgresql.JSONB, default=[]),
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_prior_authorizations_tenant', 'prior_authorizations', ['tenant_id'])
    op.create_index('ix_prior_authorizations_patient', 'prior_authorizations', ['patient_id'])
    op.create_index('ix_prior_authorizations_status', 'prior_authorizations', ['status'])
    op.create_index('ix_prior_authorizations_auth_number', 'prior_authorizations', ['auth_number'])
    op.create_index('idx_prior_authorizations_tenant_patient', 'prior_authorizations', ['tenant_id', 'patient_id'])

    # ==================== Payment Cards ====================
    op.create_table(
        'payment_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Tokenized card info
        sa.Column('token', sa.String(200), nullable=False),
        sa.Column('last_four', sa.String(4), nullable=False),
        sa.Column('card_type', sa.String(20)),
        sa.Column('expiry_month', sa.Integer),
        sa.Column('expiry_year', sa.Integer),
        # Card holder
        sa.Column('cardholder_name', sa.String(200)),
        sa.Column('billing_address', postgresql.JSONB),
        # Status
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_payment_cards_tenant', 'payment_cards', ['tenant_id'])
    op.create_index('ix_payment_cards_patient', 'payment_cards', ['patient_id'])

    # ==================== Fee Schedules ====================
    op.create_table(
        'fee_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('schedule_type', sa.String(30)),
        # Effective dates
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('termination_date', sa.Date),
        # Default for
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('payer_id', sa.String(50)),
        # Geographic adjustment
        sa.Column('locality', sa.String(10)),
        sa.Column('gpci_work', sa.Float, default=1.0),
        sa.Column('gpci_pe', sa.Float, default=1.0),
        sa.Column('gpci_mp', sa.Float, default=1.0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_fee_schedules_tenant', 'fee_schedules', ['tenant_id'])
    op.create_index('ix_fee_schedules_active', 'fee_schedules', ['is_active'])

    # ==================== Fee Schedule Rates ====================
    op.create_table(
        'fee_schedule_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fee_schedules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Code
        sa.Column('procedure_code', sa.String(10), nullable=False),
        sa.Column('modifier', sa.String(5)),
        # Amounts
        sa.Column('charge_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('expected_reimbursement', sa.Numeric(12, 2)),
        # RVUs
        sa.Column('rvu_work', sa.Float),
        sa.Column('rvu_pe', sa.Float),
        sa.Column('rvu_mp', sa.Float),
        sa.Column('rvu_total', sa.Float),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.UniqueConstraint('schedule_id', 'procedure_code', 'modifier', name='uq_fee_schedule_rate'),
    )
    op.create_index('ix_fee_schedule_rates_procedure', 'fee_schedule_rates', ['procedure_code'])

    # ==================== Payer Contracts ====================
    op.create_table(
        'payer_contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Payer info
        sa.Column('payer_id', sa.String(50), nullable=False),
        sa.Column('payer_name', sa.String(200), nullable=False),
        sa.Column('contract_name', sa.String(200)),
        # Contract terms
        sa.Column('contract_number', sa.String(50)),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('termination_date', sa.Date),
        sa.Column('auto_renew', sa.Boolean, default=True),
        sa.Column('renewal_notice_days', sa.Integer, default=90),
        # Rates
        sa.Column('rate_type', sa.String(30)),
        sa.Column('base_rate_percent', sa.Float),
        sa.Column('fee_schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fee_schedules.id')),
        # Timely filing
        sa.Column('timely_filing_days', sa.Integer, default=365),
        sa.Column('appeal_filing_days', sa.Integer, default=180),
        # Terms
        sa.Column('terms_notes', sa.Text),
        sa.Column('special_provisions', postgresql.JSONB, default={}),
        # Documents
        sa.Column('contract_document_url', sa.String(500)),
        # Status
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_payer_contracts_tenant', 'payer_contracts', ['tenant_id'])
    op.create_index('ix_payer_contracts_payer', 'payer_contracts', ['payer_id'])
    op.create_index('ix_payer_contracts_status', 'payer_contracts', ['status'])

    # ==================== Contract Rate Overrides ====================
    op.create_table(
        'contract_rate_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payer_contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('procedure_code', sa.String(10), nullable=False),
        sa.Column('modifier', sa.String(5)),
        # Override
        sa.Column('rate_type', sa.String(30)),
        sa.Column('rate_amount', sa.Numeric(12, 2)),
        sa.Column('rate_percent', sa.Float),
        # Effective dates
        sa.Column('effective_date', sa.Date),
        sa.Column('termination_date', sa.Date),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    op.create_index('ix_contract_rate_overrides_contract', 'contract_rate_overrides', ['contract_id'])
    op.create_index('ix_contract_rate_overrides_procedure', 'contract_rate_overrides', ['procedure_code'])

    # ==================== Payment Plans ====================
    op.create_table(
        'payment_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Plan details
        sa.Column('plan_name', sa.String(200)),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('down_payment', sa.Numeric(12, 2), default=0),
        sa.Column('payment_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('frequency', sa.String(20), default='monthly'),
        # Progress
        sa.Column('paid_amount', sa.Numeric(12, 2), default=0),
        sa.Column('remaining_amount', sa.Numeric(12, 2)),
        sa.Column('payments_made', sa.Integer, default=0),
        sa.Column('total_payments', sa.Integer, nullable=False),
        # Dates
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date),
        sa.Column('next_payment_date', sa.Date),
        # Status
        sa.Column('status', sa.String(20), default='active'),
        # Auto-pay
        sa.Column('auto_pay', sa.Boolean, default=False),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_cards.id')),
        # Related
        sa.Column('claim_ids', postgresql.ARRAY(postgresql.UUID), default=[]),
        sa.Column('encounter_ids', postgresql.ARRAY(postgresql.UUID), default=[]),
        # Signed agreement
        sa.Column('agreement_signed', sa.Boolean, default=False),
        sa.Column('agreement_signed_at', sa.DateTime(timezone=True)),
        sa.Column('agreement_ip_address', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_payment_plans_tenant', 'payment_plans', ['tenant_id'])
    op.create_index('ix_payment_plans_patient', 'payment_plans', ['patient_id'])
    op.create_index('ix_payment_plans_status', 'payment_plans', ['status'])

    # ==================== Claims ====================
    op.create_table(
        'claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_number', sa.String(50), unique=True, nullable=False),
        # Claim type
        sa.Column('claim_type', sa.String(20), nullable=False, default='professional'),
        # Patient info
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_account_number', sa.String(50)),
        # Subscriber info
        sa.Column('subscriber_id', postgresql.UUID(as_uuid=True)),
        sa.Column('subscriber_name', sa.String(200)),
        sa.Column('relationship_to_subscriber', sa.String(20)),
        # Insurance info
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('insurance_policies.id')),
        sa.Column('payer_id', sa.String(50), nullable=False),
        sa.Column('payer_name', sa.String(200)),
        sa.Column('member_id', sa.String(50), nullable=False),
        sa.Column('group_number', sa.String(50)),
        sa.Column('prior_auth_number', sa.String(50)),
        sa.Column('prior_auth_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prior_authorizations.id')),
        # Secondary insurance
        sa.Column('secondary_payer_id', sa.String(50)),
        sa.Column('secondary_member_id', sa.String(50)),
        sa.Column('secondary_policy_id', postgresql.UUID(as_uuid=True)),
        # Provider info
        sa.Column('billing_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('billing_provider_npi', sa.String(10), nullable=False),
        sa.Column('billing_provider_tax_id', sa.String(20)),
        sa.Column('rendering_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('rendering_provider_npi', sa.String(10)),
        sa.Column('referring_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('referring_provider_npi', sa.String(10)),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True)),
        sa.Column('facility_npi', sa.String(10)),
        # Encounter reference
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        # Dates
        sa.Column('statement_date', sa.Date),
        sa.Column('service_date_start', sa.Date, nullable=False),
        sa.Column('service_date_end', sa.Date),
        sa.Column('admission_date', sa.Date),
        sa.Column('discharge_date', sa.Date),
        # Place of service
        sa.Column('place_of_service', sa.String(5), default='11'),
        sa.Column('facility_type_code', sa.String(10)),
        # Diagnoses
        sa.Column('diagnoses', postgresql.JSONB, default=[]),
        sa.Column('principal_diagnosis', sa.String(20)),
        sa.Column('admitting_diagnosis', sa.String(20)),
        # Totals
        sa.Column('total_charge', sa.Numeric(12, 2), default=0),
        sa.Column('total_allowed', sa.Numeric(12, 2)),
        sa.Column('total_paid', sa.Numeric(12, 2), default=0),
        sa.Column('total_adjustment', sa.Numeric(12, 2), default=0),
        sa.Column('patient_responsibility', sa.Numeric(12, 2), default=0),
        sa.Column('balance', sa.Numeric(12, 2)),
        # Status
        sa.Column('status', sa.String(30), default='draft'),
        sa.Column('status_date', sa.DateTime(timezone=True)),
        sa.Column('status_reason', sa.Text),
        # Submission
        sa.Column('submission_method', sa.String(30)),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True)),
        sa.Column('payer_claim_number', sa.String(50)),
        sa.Column('clearinghouse_id', sa.String(100)),
        sa.Column('clearinghouse_claim_id', sa.String(100)),
        # Acknowledgment
        sa.Column('acknowledged_at', sa.DateTime(timezone=True)),
        sa.Column('acknowledgment_code', sa.String(10)),
        sa.Column('acknowledgment_errors', postgresql.JSONB, default=[]),
        # Adjudication
        sa.Column('adjudicated_at', sa.DateTime(timezone=True)),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
        sa.Column('check_number', sa.String(50)),
        sa.Column('eft_trace_number', sa.String(50)),
        # Denial
        sa.Column('denied_at', sa.DateTime(timezone=True)),
        sa.Column('denial_reason_codes', postgresql.ARRAY(sa.String(10)), default=[]),
        sa.Column('denial_category', sa.String(30)),
        # Appeal
        sa.Column('appeal_deadline', sa.Date),
        sa.Column('appealed_at', sa.DateTime(timezone=True)),
        sa.Column('appeal_status', sa.String(30)),
        # Notes
        sa.Column('internal_notes', sa.Text),
        sa.Column('submission_notes', sa.Text),
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_claims_tenant', 'claims', ['tenant_id'])
    op.create_index('ix_claims_patient', 'claims', ['patient_id'])
    op.create_index('ix_claims_payer', 'claims', ['payer_id'])
    op.create_index('ix_claims_status', 'claims', ['status'])
    op.create_index('idx_claims_tenant_patient', 'claims', ['tenant_id', 'patient_id'])
    op.create_index('idx_claims_service_date', 'claims', ['service_date_start'])

    # ==================== Claim Lines ====================
    op.create_table(
        'claim_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Line details
        sa.Column('line_number', sa.Integer, nullable=False),
        # Service
        sa.Column('procedure_code', sa.String(10), nullable=False),
        sa.Column('modifiers', postgresql.ARRAY(sa.String(5)), default=[]),
        sa.Column('description', sa.String(500)),
        # Revenue code
        sa.Column('revenue_code', sa.String(10)),
        # Diagnosis pointers
        sa.Column('diagnosis_pointers', postgresql.ARRAY(sa.String(5)), default=[]),
        # Service dates
        sa.Column('service_date', sa.Date, nullable=False),
        sa.Column('service_date_end', sa.Date),
        # Place of service
        sa.Column('place_of_service', sa.String(5)),
        # Units and charges
        sa.Column('units', sa.Numeric(10, 2), default=1),
        sa.Column('unit_type', sa.String(10), default='UN'),
        sa.Column('charge_amount', sa.Numeric(12, 2), nullable=False),
        # NDC for drugs
        sa.Column('ndc_code', sa.String(15)),
        sa.Column('ndc_quantity', sa.Numeric(10, 3)),
        sa.Column('ndc_unit', sa.String(5)),
        # Rendering provider
        sa.Column('rendering_provider_npi', sa.String(10)),
        # Adjudication
        sa.Column('allowed_amount', sa.Numeric(12, 2)),
        sa.Column('paid_amount', sa.Numeric(12, 2)),
        sa.Column('adjustment_amount', sa.Numeric(12, 2), default=0),
        sa.Column('patient_responsibility', sa.Numeric(12, 2)),
        sa.Column('denial_reason', sa.String(10)),
        sa.Column('remark_codes', postgresql.ARRAY(sa.String(10)), default=[]),
        # Status
        sa.Column('status', sa.String(20), default='pending'),
    )
    op.create_index('ix_claim_lines_claim', 'claim_lines', ['claim_id'])
    op.create_index('ix_claim_lines_procedure', 'claim_lines', ['procedure_code'])

    # ==================== Claim Adjustments ====================
    op.create_table(
        'claim_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claim_lines.id')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Adjustment details
        sa.Column('group_code', sa.String(5), nullable=False),
        sa.Column('reason_code', sa.String(10), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 2)),
        sa.Column('description', sa.Text),
        # Source
        sa.Column('source', sa.String(30)),
        sa.Column('remittance_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('ix_claim_adjustments_claim', 'claim_adjustments', ['claim_id'])

    # ==================== Remittance Advices ====================
    op.create_table(
        'remittance_advices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id')),
        # Payer info
        sa.Column('payer_id', sa.String(50), nullable=False),
        sa.Column('payer_name', sa.String(200)),
        # Payment info
        sa.Column('check_number', sa.String(50)),
        sa.Column('eft_trace_number', sa.String(50)),
        sa.Column('payment_method', sa.String(20)),
        sa.Column('payment_date', sa.Date),
        sa.Column('payment_amount', sa.Numeric(12, 2)),
        # Claim details from ERA
        sa.Column('payer_claim_number', sa.String(50)),
        sa.Column('patient_account_number', sa.String(50)),
        sa.Column('claim_status_code', sa.String(5)),
        # Amounts
        sa.Column('charged_amount', sa.Numeric(12, 2)),
        sa.Column('allowed_amount', sa.Numeric(12, 2)),
        sa.Column('paid_amount', sa.Numeric(12, 2)),
        sa.Column('patient_responsibility', sa.Numeric(12, 2)),
        # Adjustments summary
        sa.Column('adjustments', postgresql.JSONB, default=[]),
        sa.Column('remark_codes', postgresql.ARRAY(sa.String(10)), default=[]),
        # Processing
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('posted_at', sa.DateTime(timezone=True)),
        sa.Column('posted_by', postgresql.UUID(as_uuid=True)),
        sa.Column('auto_posted', sa.Boolean, default=False),
        # Raw data
        sa.Column('raw_835', sa.Text),
    )
    op.create_index('ix_remittance_advices_tenant', 'remittance_advices', ['tenant_id'])
    op.create_index('ix_remittance_advices_claim', 'remittance_advices', ['claim_id'])
    op.create_index('ix_remittance_advices_payer', 'remittance_advices', ['payer_id'])

    # ==================== Payments ====================
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_number', sa.String(50), unique=True),
        # Patient
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Amount
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        # Payment details
        sa.Column('payment_type', sa.String(30), nullable=False),
        sa.Column('payment_method', sa.String(30), nullable=False),
        sa.Column('payment_source', sa.String(30)),
        # Card details
        sa.Column('card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_cards.id')),
        sa.Column('card_last_four', sa.String(4)),
        sa.Column('card_type', sa.String(20)),
        # Check details
        sa.Column('check_number', sa.String(50)),
        sa.Column('bank_name', sa.String(200)),
        # Status
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('status_reason', sa.Text),
        # Processing
        sa.Column('processor', sa.String(50)),
        sa.Column('processor_transaction_id', sa.String(100)),
        sa.Column('authorization_code', sa.String(50)),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        # Allocation
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id')),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('payment_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_plans.id')),
        # Receipt
        sa.Column('receipt_number', sa.String(50)),
        sa.Column('receipt_sent', sa.Boolean, default=False),
        sa.Column('receipt_sent_at', sa.DateTime(timezone=True)),
        # Refund
        sa.Column('refund_amount', sa.Numeric(12, 2)),
        sa.Column('refund_reason', sa.Text),
        sa.Column('refunded_at', sa.DateTime(timezone=True)),
        sa.Column('refund_transaction_id', sa.String(100)),
        # Metadata
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_payments_tenant', 'payments', ['tenant_id'])
    op.create_index('ix_payments_patient', 'payments', ['patient_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('idx_payments_tenant_patient', 'payments', ['tenant_id', 'patient_id'])
    op.create_index('idx_payments_date', 'payments', ['created_at'])

    # ==================== Payment Plan Schedules ====================
    op.create_table(
        'payment_plan_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence', sa.Integer, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.String(20), default='scheduled'),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id')),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_payment_plan_schedules_plan', 'payment_plan_schedules', ['plan_id'])
    op.create_index('ix_payment_plan_schedules_status', 'payment_plan_schedules', ['status'])

    # ==================== Patient Statements ====================
    op.create_table(
        'patient_statements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('statement_number', sa.String(50), unique=True),
        # Statement period
        sa.Column('statement_date', sa.Date, nullable=False),
        sa.Column('period_start', sa.Date),
        sa.Column('period_end', sa.Date),
        sa.Column('due_date', sa.Date),
        # Amounts
        sa.Column('previous_balance', sa.Numeric(12, 2), default=0),
        sa.Column('new_charges', sa.Numeric(12, 2), default=0),
        sa.Column('payments_received', sa.Numeric(12, 2), default=0),
        sa.Column('adjustments', sa.Numeric(12, 2), default=0),
        sa.Column('current_balance', sa.Numeric(12, 2), nullable=False),
        sa.Column('amount_due', sa.Numeric(12, 2), nullable=False),
        sa.Column('minimum_payment', sa.Numeric(12, 2)),
        # Aging
        sa.Column('current', sa.Numeric(12, 2), default=0),
        sa.Column('days_30', sa.Numeric(12, 2), default=0),
        sa.Column('days_60', sa.Numeric(12, 2), default=0),
        sa.Column('days_90', sa.Numeric(12, 2), default=0),
        sa.Column('days_120_plus', sa.Numeric(12, 2), default=0),
        # Line items
        sa.Column('line_items', postgresql.JSONB, default=[]),
        # Status
        sa.Column('status', sa.String(20), default='generated'),
        sa.Column('dunning_level', sa.Integer, default=0),
        # Delivery
        sa.Column('delivery_method', sa.String(20), default='email'),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('viewed_at', sa.DateTime(timezone=True)),
        # PDF
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('pdf_generated_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_patient_statements_tenant', 'patient_statements', ['tenant_id'])
    op.create_index('ix_patient_statements_patient', 'patient_statements', ['patient_id'])
    op.create_index('idx_patient_statements_tenant_patient', 'patient_statements', ['tenant_id', 'patient_id'])
    op.create_index('idx_patient_statements_date', 'patient_statements', ['statement_date'])

    # ==================== Denial Records ====================
    op.create_table(
        'denial_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('claim_line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('claim_lines.id')),
        # Denial info
        sa.Column('denial_date', sa.Date, nullable=False),
        sa.Column('denial_reason_code', sa.String(10), nullable=False),
        sa.Column('denial_reason_description', sa.Text),
        sa.Column('denial_category', sa.String(30)),
        # Amounts
        sa.Column('denied_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('potential_recovery', sa.Numeric(12, 2)),
        # Appeal
        sa.Column('appeal_deadline', sa.Date),
        sa.Column('is_appealable', sa.Boolean, default=True),
        sa.Column('appeal_submitted', sa.Boolean, default=False),
        sa.Column('appeal_submitted_at', sa.DateTime(timezone=True)),
        sa.Column('appeal_status', sa.String(30)),
        sa.Column('appeal_outcome', sa.String(30)),
        sa.Column('recovered_amount', sa.Numeric(12, 2)),
        # Assignment
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('assigned_at', sa.DateTime(timezone=True)),
        # Resolution
        sa.Column('resolution_status', sa.String(30), default='open'),
        sa.Column('resolution_date', sa.Date),
        sa.Column('resolution_notes', sa.Text),
        # Root cause
        sa.Column('root_cause', sa.String(100)),
        sa.Column('preventable', sa.Boolean),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_denial_records_tenant', 'denial_records', ['tenant_id'])
    op.create_index('ix_denial_records_claim', 'denial_records', ['claim_id'])
    op.create_index('ix_denial_records_status', 'denial_records', ['resolution_status'])
    op.create_index('ix_denial_records_category', 'denial_records', ['denial_category'])

    # ==================== Billing Audit Logs ====================
    op.create_table(
        'billing_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        # What
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        # Who
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_name', sa.String(200)),
        sa.Column('user_role', sa.String(50)),
        # Details
        sa.Column('old_values', postgresql.JSONB),
        sa.Column('new_values', postgresql.JSONB),
        sa.Column('change_summary', sa.Text),
        # Context
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('session_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_billing_audit_logs_tenant', 'billing_audit_logs', ['tenant_id'])
    op.create_index('idx_billing_audit_logs_entity', 'billing_audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_billing_audit_logs_date', 'billing_audit_logs', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('billing_audit_logs')
    op.drop_table('denial_records')
    op.drop_table('patient_statements')
    op.drop_table('payment_plan_schedules')
    op.drop_table('payments')
    op.drop_table('remittance_advices')
    op.drop_table('claim_adjustments')
    op.drop_table('claim_lines')
    op.drop_table('claims')
    op.drop_table('payment_plans')
    op.drop_table('contract_rate_overrides')
    op.drop_table('payer_contracts')
    op.drop_table('fee_schedule_rates')
    op.drop_table('fee_schedules')
    op.drop_table('payment_cards')
    op.drop_table('prior_authorizations')
    op.drop_table('eligibility_verifications')
    op.drop_table('insurance_policies')
