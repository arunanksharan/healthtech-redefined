"""Advanced Analytics Tables

Revision ID: 008_advanced_analytics
Revises: 007_medical_ai
Create Date: 2024-11-25

EPIC-011: Advanced Analytics Platform

Tables:
- Dimension Tables (Data Warehouse):
  - dim_date: Date dimension for time-based analysis
  - dim_time: Time of day dimension
  - dim_patients: Patient dimension (Type 2 SCD)
  - dim_providers: Provider dimension
  - dim_facilities: Facility dimension
  - dim_diagnoses: Diagnosis/ICD dimension
  - dim_procedures: Procedure/CPT dimension
  - dim_payers: Payer dimension

- Fact Tables (Data Warehouse):
  - fact_encounters: Encounter-level facts
  - fact_quality_measures: Quality measure results

- Operational Tables:
  - executive_dashboards: Dashboard configurations
  - kpi_snapshots: Historical KPI values
  - quality_measures: Quality measure definitions
  - quality_measure_results: Quality measure outcomes
  - provider_scorecards: Provider performance tracking
  - patient_risk_profiles: Risk stratification data
  - care_gaps: Care gap identification
  - chronic_disease_registries: Disease registry tracking
  - sdoh_assessments: Social determinants assessments
  - revenue_snapshots: Financial performance snapshots
  - denial_records: Claims denial tracking
  - ar_aging_snapshots: AR aging history
  - department_productivity: Operational metrics
  - resource_utilization: Resource usage tracking
  - patient_flow_events: Patient flow tracking
  - ml_models: Predictive model registry
  - ml_predictions: Prediction results
  - model_drift_metrics: Model monitoring
  - ab_test_results: Model A/B tests
  - report_definitions: Custom report configs
  - report_executions: Report run history
  - scheduled_reports: Report scheduling
  - report_templates: Reusable templates
  - analytics_audit_log: Analytics access logging
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '008_advanced_analytics'
down_revision = '007_medical_ai'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Enums ====================

    # Metric Trend
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE metric_trend AS ENUM (
                'improving', 'declining', 'stable', 'volatile'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Performance Level
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE performance_level AS ENUM (
                'exceeding', 'meeting', 'below', 'critical'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Measure Category
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_category AS ENUM (
                'process', 'outcome', 'structure', 'patient_experience', 'safety'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Measure Program
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_program AS ENUM (
                'mips', 'aco', 'hedis', 'cms_core', 'tjc', 'nqf', 'pqrs', 'meaningful_use'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Performance Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE performance_status AS ENUM (
                'excellent', 'good', 'fair', 'poor', 'critical'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Care Gap Priority
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE care_gap_priority AS ENUM (
                'critical', 'high', 'medium', 'low'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Care Gap Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE care_gap_status AS ENUM (
                'open', 'scheduled', 'in_progress', 'closed', 'patient_declined'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Chronic Condition
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE chronic_condition AS ENUM (
                'diabetes', 'hypertension', 'heart_failure', 'copd', 'asthma',
                'ckd', 'depression', 'obesity', 'cancer', 'stroke'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Payer Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE payer_type AS ENUM (
                'medicare', 'medicaid', 'commercial', 'self_pay', 'workers_comp',
                'tricare', 'va', 'other_government', 'no_fault', 'uninsured'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Denial Reason
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE denial_reason AS ENUM (
                'eligibility', 'authorization', 'coding_error', 'medical_necessity',
                'duplicate', 'timely_filing', 'missing_info', 'bundling',
                'modifier', 'coordination_benefits', 'out_of_network', 'other'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # AR Aging Bucket
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ar_aging_bucket AS ENUM (
                'current', 'days_31_60', 'days_61_90', 'days_91_120', 'days_over_120'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Department Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE department_type AS ENUM (
                'emergency', 'inpatient', 'outpatient', 'surgery', 'radiology',
                'laboratory', 'pharmacy', 'rehabilitation', 'behavioral_health', 'primary_care'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Resource Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE resource_type AS ENUM (
                'bed', 'or_room', 'exam_room', 'imaging_equipment', 'ventilator',
                'infusion_pump', 'wheelchair', 'stretcher', 'isolation_room', 'icu_bed'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Model Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ml_model_type AS ENUM (
                'readmission', 'length_of_stay', 'no_show', 'deterioration',
                'cost', 'mortality', 'sepsis', 'fall_risk', 'icu_transfer', 'custom'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Model Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ml_model_status AS ENUM (
                'development', 'validation', 'staging', 'production', 'deprecated', 'archived'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Report Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE report_type AS ENUM (
                'dashboard', 'tabular', 'summary', 'detail', 'trending', 'comparison', 'scorecard'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Visualization Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE visualization_type AS ENUM (
                'bar_chart', 'line_chart', 'pie_chart', 'donut_chart', 'area_chart',
                'scatter_plot', 'heat_map', 'treemap', 'funnel', 'gauge',
                'table', 'pivot_table', 'kpi_card', 'sparkline', 'waterfall',
                'sankey', 'bullet_chart', 'radar_chart', 'box_plot', 'histogram'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Export Format
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE export_format AS ENUM (
                'pdf', 'excel', 'csv', 'powerpoint', 'json', 'xml', 'png', 'html'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Schedule Frequency
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE schedule_frequency AS ENUM (
                'once', 'daily', 'weekly', 'biweekly', 'monthly', 'quarterly', 'annually'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==================== Dimension Tables ====================

    # Dim Date - Date dimension for time-based analysis
    op.create_table(
        'dim_date',
        sa.Column('date_key', sa.Integer, primary_key=True),
        sa.Column('full_date', sa.Date, nullable=False, unique=True),
        sa.Column('day_of_week', sa.SmallInteger, nullable=False),
        sa.Column('day_name', sa.String(10), nullable=False),
        sa.Column('day_of_month', sa.SmallInteger, nullable=False),
        sa.Column('day_of_year', sa.SmallInteger, nullable=False),
        sa.Column('week_of_year', sa.SmallInteger, nullable=False),
        sa.Column('week_of_month', sa.SmallInteger, nullable=False),
        sa.Column('month', sa.SmallInteger, nullable=False),
        sa.Column('month_name', sa.String(10), nullable=False),
        sa.Column('month_abbrev', sa.String(3), nullable=False),
        sa.Column('quarter', sa.SmallInteger, nullable=False),
        sa.Column('quarter_name', sa.String(2), nullable=False),
        sa.Column('year', sa.SmallInteger, nullable=False),
        sa.Column('year_month', sa.String(7), nullable=False),
        sa.Column('year_quarter', sa.String(7), nullable=False),
        sa.Column('is_weekend', sa.Boolean, default=False),
        sa.Column('is_holiday', sa.Boolean, default=False),
        sa.Column('holiday_name', sa.String(50), nullable=True),
        sa.Column('fiscal_year', sa.SmallInteger, nullable=True),
        sa.Column('fiscal_quarter', sa.SmallInteger, nullable=True),
        sa.Column('fiscal_month', sa.SmallInteger, nullable=True),
    )

    op.create_index('ix_dim_date_full', 'dim_date', ['full_date'])
    op.create_index('ix_dim_date_year_month', 'dim_date', ['year', 'month'])

    # Dim Time - Time of day dimension
    op.create_table(
        'dim_time',
        sa.Column('time_key', sa.Integer, primary_key=True),
        sa.Column('full_time', sa.Time, nullable=False, unique=True),
        sa.Column('hour', sa.SmallInteger, nullable=False),
        sa.Column('minute', sa.SmallInteger, nullable=False),
        sa.Column('hour_12', sa.SmallInteger, nullable=False),
        sa.Column('am_pm', sa.String(2), nullable=False),
        sa.Column('time_of_day', sa.String(20), nullable=False),  # Morning, Afternoon, Evening, Night
        sa.Column('shift', sa.String(20), nullable=True),  # Day Shift, Night Shift, etc.
        sa.Column('is_business_hours', sa.Boolean, default=False),
    )

    op.create_index('ix_dim_time_hour', 'dim_time', ['hour'])

    # Dim Patients - Patient dimension (Type 2 SCD)
    op.create_table(
        'dim_patients',
        sa.Column('patient_key', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mrn', sa.String(50), nullable=True),

        # Demographics
        sa.Column('age_at_snapshot', sa.Integer, nullable=True),
        sa.Column('age_group', sa.String(20), nullable=True),  # 0-17, 18-34, 35-49, 50-64, 65+
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('race', sa.String(50), nullable=True),
        sa.Column('ethnicity', sa.String(50), nullable=True),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('marital_status', sa.String(30), nullable=True),

        # Geographic
        sa.Column('zip_code', sa.String(10), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('county', sa.String(100), nullable=True),

        # Risk
        sa.Column('risk_score', sa.Float, nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('hcc_count', sa.Integer, default=0),

        # Payer
        sa.Column('primary_payer_type', sa.Enum('medicare', 'medicaid', 'commercial', 'self_pay',
                                                 'workers_comp', 'tricare', 'va', 'other_government',
                                                 'no_fault', 'uninsured', name='payer_type'), nullable=True),
        sa.Column('primary_payer_name', sa.String(100), nullable=True),

        # SCD fields
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('expiration_date', sa.Date, nullable=True),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_dim_patients_tenant', 'dim_patients', ['tenant_id'])
    op.create_index('ix_dim_patients_patient_id', 'dim_patients', ['patient_id'])
    op.create_index('ix_dim_patients_current', 'dim_patients', ['patient_id', 'is_current'])
    op.create_index('ix_dim_patients_risk', 'dim_patients', ['risk_level'])

    # Dim Providers - Provider dimension
    op.create_table(
        'dim_providers',
        sa.Column('provider_key', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('npi', sa.String(10), nullable=True),

        # Provider info
        sa.Column('provider_name', sa.String(200), nullable=True),
        sa.Column('provider_type', sa.String(50), nullable=True),  # Physician, NP, PA, etc.
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('subspecialty', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),

        # Credentials
        sa.Column('credentials', sa.String(50), nullable=True),  # MD, DO, NP, etc.
        sa.Column('board_certified', sa.Boolean, default=False),

        # Location
        sa.Column('primary_facility', sa.String(200), nullable=True),
        sa.Column('primary_location', sa.String(200), nullable=True),

        # SCD fields
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('expiration_date', sa.Date, nullable=True),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_dim_providers_tenant', 'dim_providers', ['tenant_id'])
    op.create_index('ix_dim_providers_provider_id', 'dim_providers', ['provider_id'])
    op.create_index('ix_dim_providers_npi', 'dim_providers', ['npi'])
    op.create_index('ix_dim_providers_specialty', 'dim_providers', ['specialty'])

    # Dim Facilities - Facility dimension
    op.create_table(
        'dim_facilities',
        sa.Column('facility_key', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Facility info
        sa.Column('facility_name', sa.String(200), nullable=False),
        sa.Column('facility_type', sa.String(50), nullable=True),  # Hospital, Clinic, ASC, etc.
        sa.Column('facility_subtype', sa.String(50), nullable=True),

        # Location
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip_code', sa.String(10), nullable=True),
        sa.Column('region', sa.String(50), nullable=True),

        # Capacity
        sa.Column('bed_count', sa.Integer, nullable=True),
        sa.Column('staffed_beds', sa.Integer, nullable=True),

        # Classification
        sa.Column('teaching_status', sa.Boolean, default=False),
        sa.Column('trauma_level', sa.String(10), nullable=True),
        sa.Column('cms_certification_number', sa.String(20), nullable=True),

        # SCD fields
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('expiration_date', sa.Date, nullable=True),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_dim_facilities_tenant', 'dim_facilities', ['tenant_id'])
    op.create_index('ix_dim_facilities_facility_id', 'dim_facilities', ['facility_id'])
    op.create_index('ix_dim_facilities_type', 'dim_facilities', ['facility_type'])

    # Dim Diagnoses - Diagnosis/ICD dimension
    op.create_table(
        'dim_diagnoses',
        sa.Column('diagnosis_key', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('icd10_code', sa.String(10), nullable=False, unique=True),
        sa.Column('icd10_description', sa.String(500), nullable=True),
        sa.Column('icd10_chapter', sa.String(100), nullable=True),
        sa.Column('icd10_category', sa.String(100), nullable=True),
        sa.Column('icd9_code', sa.String(10), nullable=True),

        # Classification
        sa.Column('is_chronic', sa.Boolean, default=False),
        sa.Column('is_acute', sa.Boolean, default=False),
        sa.Column('is_mental_health', sa.Boolean, default=False),
        sa.Column('is_substance_use', sa.Boolean, default=False),

        # Risk adjustment
        sa.Column('hcc_code', sa.String(10), nullable=True),
        sa.Column('hcc_description', sa.String(200), nullable=True),
        sa.Column('hcc_coefficient', sa.Float, nullable=True),

        # Metadata
        sa.Column('effective_date', sa.Date, nullable=True),
        sa.Column('termination_date', sa.Date, nullable=True),
    )

    op.create_index('ix_dim_diagnoses_icd10', 'dim_diagnoses', ['icd10_code'])
    op.create_index('ix_dim_diagnoses_hcc', 'dim_diagnoses', ['hcc_code'])

    # Dim Procedures - Procedure/CPT dimension
    op.create_table(
        'dim_procedures',
        sa.Column('procedure_key', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('cpt_code', sa.String(10), nullable=False, unique=True),
        sa.Column('cpt_description', sa.String(500), nullable=True),
        sa.Column('cpt_category', sa.String(100), nullable=True),
        sa.Column('cpt_section', sa.String(100), nullable=True),

        # Classification
        sa.Column('is_surgical', sa.Boolean, default=False),
        sa.Column('is_e_m', sa.Boolean, default=False),  # Evaluation & Management
        sa.Column('is_imaging', sa.Boolean, default=False),
        sa.Column('is_lab', sa.Boolean, default=False),

        # Relative Value Units
        sa.Column('work_rvu', sa.Float, nullable=True),
        sa.Column('practice_expense_rvu', sa.Float, nullable=True),
        sa.Column('malpractice_rvu', sa.Float, nullable=True),
        sa.Column('total_rvu', sa.Float, nullable=True),

        # Pricing
        sa.Column('national_payment_amount', sa.Float, nullable=True),

        # Metadata
        sa.Column('effective_date', sa.Date, nullable=True),
        sa.Column('termination_date', sa.Date, nullable=True),
    )

    op.create_index('ix_dim_procedures_cpt', 'dim_procedures', ['cpt_code'])
    op.create_index('ix_dim_procedures_category', 'dim_procedures', ['cpt_category'])

    # Dim Payers - Payer dimension
    op.create_table(
        'dim_payers',
        sa.Column('payer_key', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payer_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Payer info
        sa.Column('payer_name', sa.String(200), nullable=False),
        sa.Column('payer_type', sa.Enum('medicare', 'medicaid', 'commercial', 'self_pay',
                                        'workers_comp', 'tricare', 'va', 'other_government',
                                        'no_fault', 'uninsured', name='payer_type'), nullable=True),

        # Plan info
        sa.Column('plan_name', sa.String(200), nullable=True),
        sa.Column('plan_type', sa.String(50), nullable=True),  # HMO, PPO, EPO, POS, etc.

        # Contract
        sa.Column('contract_type', sa.String(50), nullable=True),
        sa.Column('fee_schedule_type', sa.String(50), nullable=True),

        # SCD fields
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('expiration_date', sa.Date, nullable=True),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_dim_payers_tenant', 'dim_payers', ['tenant_id'])
    op.create_index('ix_dim_payers_payer_id', 'dim_payers', ['payer_id'])
    op.create_index('ix_dim_payers_type', 'dim_payers', ['payer_type'])

    # ==================== Fact Tables ====================

    # Fact Encounters - Encounter-level facts
    op.create_table(
        'fact_encounters',
        sa.Column('encounter_fact_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Dimension keys
        sa.Column('patient_key', sa.BigInteger, nullable=True),
        sa.Column('provider_key', sa.BigInteger, nullable=True),
        sa.Column('facility_key', sa.BigInteger, nullable=True),
        sa.Column('payer_key', sa.BigInteger, nullable=True),
        sa.Column('admission_date_key', sa.Integer, nullable=True),
        sa.Column('discharge_date_key', sa.Integer, nullable=True),
        sa.Column('admission_time_key', sa.Integer, nullable=True),
        sa.Column('discharge_time_key', sa.Integer, nullable=True),

        # Encounter details
        sa.Column('encounter_type', sa.String(50), nullable=True),  # Inpatient, Outpatient, ED, etc.
        sa.Column('encounter_class', sa.String(50), nullable=True),
        sa.Column('admission_type', sa.String(50), nullable=True),
        sa.Column('admission_source', sa.String(50), nullable=True),
        sa.Column('discharge_disposition', sa.String(50), nullable=True),

        # Diagnoses
        sa.Column('primary_diagnosis_key', sa.BigInteger, nullable=True),
        sa.Column('drg_code', sa.String(10), nullable=True),
        sa.Column('drg_weight', sa.Float, nullable=True),
        sa.Column('diagnosis_count', sa.Integer, default=0),

        # Procedures
        sa.Column('primary_procedure_key', sa.BigInteger, nullable=True),
        sa.Column('procedure_count', sa.Integer, default=0),

        # Measures
        sa.Column('length_of_stay', sa.Float, nullable=True),
        sa.Column('ed_wait_time_minutes', sa.Float, nullable=True),
        sa.Column('time_to_provider_minutes', sa.Float, nullable=True),

        # Financial
        sa.Column('total_charges', sa.Float, default=0),
        sa.Column('total_cost', sa.Float, default=0),
        sa.Column('total_payments', sa.Float, default=0),
        sa.Column('total_adjustments', sa.Float, default=0),
        sa.Column('patient_responsibility', sa.Float, default=0),
        sa.Column('profit_margin', sa.Float, nullable=True),

        # Outcomes
        sa.Column('readmission_30_day', sa.Boolean, default=False),
        sa.Column('readmission_90_day', sa.Boolean, default=False),
        sa.Column('mortality', sa.Boolean, default=False),
        sa.Column('left_ama', sa.Boolean, default=False),

        # Risk
        sa.Column('severity_of_illness', sa.String(20), nullable=True),
        sa.Column('risk_of_mortality', sa.String(20), nullable=True),
        sa.Column('acuity_level', sa.SmallInteger, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_fact_encounters_tenant', 'fact_encounters', ['tenant_id'])
    op.create_index('ix_fact_encounters_encounter_id', 'fact_encounters', ['encounter_id'])
    op.create_index('ix_fact_encounters_patient', 'fact_encounters', ['patient_key'])
    op.create_index('ix_fact_encounters_provider', 'fact_encounters', ['provider_key'])
    op.create_index('ix_fact_encounters_admission_date', 'fact_encounters', ['admission_date_key'])
    op.create_index('ix_fact_encounters_type', 'fact_encounters', ['encounter_type'])
    op.create_index('ix_fact_encounters_readmission', 'fact_encounters', ['readmission_30_day'])

    # Fact Quality Measures - Quality measure results
    op.create_table(
        'fact_quality_measures',
        sa.Column('quality_fact_id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Dimension keys
        sa.Column('measure_key', sa.BigInteger, nullable=False),
        sa.Column('provider_key', sa.BigInteger, nullable=True),
        sa.Column('facility_key', sa.BigInteger, nullable=True),
        sa.Column('measurement_date_key', sa.Integer, nullable=False),

        # Period
        sa.Column('reporting_period_start', sa.Date, nullable=False),
        sa.Column('reporting_period_end', sa.Date, nullable=False),

        # Population
        sa.Column('denominator', sa.Integer, nullable=False),
        sa.Column('denominator_exclusions', sa.Integer, default=0),
        sa.Column('denominator_exceptions', sa.Integer, default=0),
        sa.Column('numerator', sa.Integer, nullable=False),

        # Performance
        sa.Column('performance_rate', sa.Float, nullable=False),
        sa.Column('performance_rate_adjusted', sa.Float, nullable=True),
        sa.Column('benchmark_rate', sa.Float, nullable=True),
        sa.Column('variance_from_benchmark', sa.Float, nullable=True),
        sa.Column('percentile_rank', sa.SmallInteger, nullable=True),

        # Status
        sa.Column('performance_status', sa.Enum('excellent', 'good', 'fair', 'poor', 'critical',
                                                 name='performance_status'), nullable=True),
        sa.Column('star_rating', sa.SmallInteger, nullable=True),

        # Trends
        sa.Column('prior_period_rate', sa.Float, nullable=True),
        sa.Column('trend_direction', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                              name='metric_trend'), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_fact_quality_tenant', 'fact_quality_measures', ['tenant_id'])
    op.create_index('ix_fact_quality_measure', 'fact_quality_measures', ['measure_key'])
    op.create_index('ix_fact_quality_provider', 'fact_quality_measures', ['provider_key'])
    op.create_index('ix_fact_quality_date', 'fact_quality_measures', ['measurement_date_key'])
    op.create_index('ix_fact_quality_period', 'fact_quality_measures', ['reporting_period_start', 'reporting_period_end'])

    # ==================== Operational Tables ====================

    # Executive Dashboards - Dashboard configurations
    op.create_table(
        'executive_dashboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Dashboard info
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('dashboard_type', sa.String(50), nullable=False),  # Executive, Clinical, Financial, etc.

        # Layout
        sa.Column('layout_config', postgresql.JSONB, default={}),
        sa.Column('widget_configs', postgresql.JSONB, default=[]),

        # KPIs
        sa.Column('kpi_ids', postgresql.ARRAY(sa.String), default=[]),

        # Filters
        sa.Column('default_filters', postgresql.JSONB, default={}),
        sa.Column('filter_configs', postgresql.JSONB, default=[]),

        # Sharing
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('shared_with_roles', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('shared_with_users', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_exec_dashboards_tenant', 'executive_dashboards', ['tenant_id'])
    op.create_index('ix_exec_dashboards_user', 'executive_dashboards', ['user_id'])
    op.create_index('ix_exec_dashboards_type', 'executive_dashboards', ['dashboard_type'])

    # KPI Snapshots - Historical KPI values
    op.create_table(
        'kpi_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # KPI reference
        sa.Column('kpi_id', sa.String(100), nullable=False),
        sa.Column('kpi_name', sa.String(200), nullable=False),
        sa.Column('kpi_category', sa.String(50), nullable=False),  # Financial, Clinical, Operational, Quality

        # Period
        sa.Column('snapshot_date', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),  # Daily, Weekly, Monthly, Quarterly
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),

        # Values
        sa.Column('current_value', sa.Float, nullable=False),
        sa.Column('previous_value', sa.Float, nullable=True),
        sa.Column('target_value', sa.Float, nullable=True),
        sa.Column('benchmark_value', sa.Float, nullable=True),

        # Analysis
        sa.Column('variance_from_target', sa.Float, nullable=True),
        sa.Column('variance_pct', sa.Float, nullable=True),
        sa.Column('trend', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                   name='metric_trend'), nullable=True),
        sa.Column('performance_level', sa.Enum('exceeding', 'meeting', 'below', 'critical',
                                                name='performance_level'), nullable=True),

        # Context
        sa.Column('data_points', sa.Integer, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_kpi_snapshots_tenant', 'kpi_snapshots', ['tenant_id'])
    op.create_index('ix_kpi_snapshots_kpi', 'kpi_snapshots', ['kpi_id'])
    op.create_index('ix_kpi_snapshots_date', 'kpi_snapshots', ['snapshot_date'])
    op.create_index('ix_kpi_snapshots_category', 'kpi_snapshots', ['kpi_category'])
    op.create_unique_constraint('uq_kpi_snapshot', 'kpi_snapshots', ['tenant_id', 'kpi_id', 'snapshot_date'])

    # Quality Measures - Quality measure definitions
    op.create_table(
        'quality_measures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Measure identification
        sa.Column('measure_id', sa.String(50), nullable=False),
        sa.Column('measure_name', sa.String(300), nullable=False),
        sa.Column('measure_description', sa.Text, nullable=True),
        sa.Column('measure_version', sa.String(20), nullable=True),

        # Classification
        sa.Column('category', sa.Enum('process', 'outcome', 'structure', 'patient_experience', 'safety',
                                       name='measure_category'), nullable=False),
        sa.Column('program', sa.Enum('mips', 'aco', 'hedis', 'cms_core', 'tjc', 'nqf', 'pqrs', 'meaningful_use',
                                      name='measure_program'), nullable=False),

        # Specifications
        sa.Column('numerator_criteria', postgresql.JSONB, default={}),
        sa.Column('denominator_criteria', postgresql.JSONB, default={}),
        sa.Column('exclusion_criteria', postgresql.JSONB, default={}),
        sa.Column('exception_criteria', postgresql.JSONB, default={}),

        # Benchmarks
        sa.Column('benchmark_percentile_25', sa.Float, nullable=True),
        sa.Column('benchmark_percentile_50', sa.Float, nullable=True),
        sa.Column('benchmark_percentile_75', sa.Float, nullable=True),
        sa.Column('benchmark_percentile_90', sa.Float, nullable=True),
        sa.Column('national_average', sa.Float, nullable=True),

        # Scoring
        sa.Column('higher_is_better', sa.Boolean, default=True),
        sa.Column('weight', sa.Float, default=1.0),
        sa.Column('max_points', sa.Integer, nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('effective_date', sa.Date, nullable=True),
        sa.Column('termination_date', sa.Date, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_quality_measures_tenant', 'quality_measures', ['tenant_id'])
    op.create_index('ix_quality_measures_measure_id', 'quality_measures', ['measure_id'])
    op.create_index('ix_quality_measures_program', 'quality_measures', ['program'])
    op.create_index('ix_quality_measures_category', 'quality_measures', ['category'])
    op.create_unique_constraint('uq_quality_measure', 'quality_measures', ['tenant_id', 'measure_id'])

    # Provider Scorecards - Provider performance tracking
    op.create_table(
        'provider_scorecards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Period
        sa.Column('scorecard_date', sa.Date, nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),

        # Overall scores
        sa.Column('overall_score', sa.Float, nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('efficiency_score', sa.Float, nullable=True),
        sa.Column('patient_experience_score', sa.Float, nullable=True),
        sa.Column('cost_score', sa.Float, nullable=True),

        # Rankings
        sa.Column('peer_rank', sa.Integer, nullable=True),
        sa.Column('peer_group_size', sa.Integer, nullable=True),
        sa.Column('percentile_rank', sa.SmallInteger, nullable=True),

        # Measure performance
        sa.Column('measure_results', postgresql.JSONB, default=[]),
        sa.Column('measures_meeting_benchmark', sa.Integer, default=0),
        sa.Column('measures_below_benchmark', sa.Integer, default=0),
        sa.Column('total_measures', sa.Integer, default=0),

        # Patient panel
        sa.Column('panel_size', sa.Integer, nullable=True),
        sa.Column('high_risk_patients', sa.Integer, nullable=True),
        sa.Column('care_gaps_closed', sa.Integer, nullable=True),

        # Financial
        sa.Column('total_rvu', sa.Float, nullable=True),
        sa.Column('avg_cost_per_patient', sa.Float, nullable=True),

        # Trends
        sa.Column('trend', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                   name='metric_trend'), nullable=True),
        sa.Column('prior_period_score', sa.Float, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_provider_scorecards_tenant', 'provider_scorecards', ['tenant_id'])
    op.create_index('ix_provider_scorecards_provider', 'provider_scorecards', ['provider_id'])
    op.create_index('ix_provider_scorecards_date', 'provider_scorecards', ['scorecard_date'])
    op.create_unique_constraint('uq_provider_scorecard', 'provider_scorecards', ['tenant_id', 'provider_id', 'scorecard_date'])

    # Patient Risk Profiles - Risk stratification data
    op.create_table(
        'patient_risk_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Assessment
        sa.Column('assessment_date', sa.Date, nullable=False),
        sa.Column('assessment_source', sa.String(50), nullable=True),  # Algorithm, Manual, Hybrid

        # Risk scores
        sa.Column('overall_risk_score', sa.Float, nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),  # Very Low, Low, Moderate, High, Very High
        sa.Column('risk_percentile', sa.SmallInteger, nullable=True),

        # Component scores
        sa.Column('clinical_risk_score', sa.Float, nullable=True),
        sa.Column('utilization_risk_score', sa.Float, nullable=True),
        sa.Column('social_risk_score', sa.Float, nullable=True),
        sa.Column('behavioral_risk_score', sa.Float, nullable=True),

        # Predictive scores
        sa.Column('predicted_cost', sa.Float, nullable=True),
        sa.Column('readmission_probability', sa.Float, nullable=True),
        sa.Column('ed_visit_probability', sa.Float, nullable=True),
        sa.Column('hospitalization_probability', sa.Float, nullable=True),

        # HCC/RAF
        sa.Column('hcc_risk_score', sa.Float, nullable=True),
        sa.Column('hcc_codes', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('raf_score', sa.Float, nullable=True),

        # Chronic conditions
        sa.Column('chronic_conditions', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('chronic_condition_count', sa.Integer, default=0),
        sa.Column('comorbidity_index', sa.Float, nullable=True),  # Charlson, Elixhauser

        # Risk factors
        sa.Column('risk_factors', postgresql.JSONB, default=[]),

        # Recommended interventions
        sa.Column('interventions', postgresql.JSONB, default=[]),
        sa.Column('care_program_eligibility', postgresql.ARRAY(sa.String), default=[]),

        # Trends
        sa.Column('prior_risk_score', sa.Float, nullable=True),
        sa.Column('risk_trend', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                         name='metric_trend'), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_risk_profiles_tenant', 'patient_risk_profiles', ['tenant_id'])
    op.create_index('ix_risk_profiles_patient', 'patient_risk_profiles', ['patient_id'])
    op.create_index('ix_risk_profiles_date', 'patient_risk_profiles', ['assessment_date'])
    op.create_index('ix_risk_profiles_level', 'patient_risk_profiles', ['risk_level'])
    op.create_index('ix_risk_profiles_score', 'patient_risk_profiles', ['overall_risk_score'])

    # Care Gaps - Care gap identification
    op.create_table(
        'care_gaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Gap identification
        sa.Column('gap_type', sa.String(100), nullable=False),  # Screening, Vaccination, Follow-up, etc.
        sa.Column('gap_name', sa.String(300), nullable=False),
        sa.Column('gap_description', sa.Text, nullable=True),

        # Clinical details
        sa.Column('measure_id', sa.String(50), nullable=True),
        sa.Column('condition', sa.String(100), nullable=True),
        sa.Column('recommended_service', sa.String(200), nullable=True),
        sa.Column('cpt_codes', postgresql.ARRAY(sa.String), default=[]),

        # Priority
        sa.Column('priority', sa.Enum('critical', 'high', 'medium', 'low',
                                       name='care_gap_priority'), nullable=False),
        sa.Column('priority_score', sa.Float, nullable=True),

        # Timing
        sa.Column('identified_date', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('last_completed_date', sa.Date, nullable=True),
        sa.Column('days_overdue', sa.Integer, nullable=True),

        # Status
        sa.Column('status', sa.Enum('open', 'scheduled', 'in_progress', 'closed', 'patient_declined',
                                     name='care_gap_status'), nullable=False, default='open'),
        sa.Column('closed_date', sa.Date, nullable=True),
        sa.Column('closed_reason', sa.String(100), nullable=True),

        # Outreach
        sa.Column('outreach_attempts', sa.Integer, default=0),
        sa.Column('last_outreach_date', sa.Date, nullable=True),
        sa.Column('next_outreach_date', sa.Date, nullable=True),
        sa.Column('outreach_history', postgresql.JSONB, default=[]),

        # Financial impact
        sa.Column('estimated_revenue', sa.Float, nullable=True),
        sa.Column('quality_points', sa.Float, nullable=True),

        # Attribution
        sa.Column('attributed_provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('care_team', postgresql.JSONB, default={}),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_care_gaps_tenant', 'care_gaps', ['tenant_id'])
    op.create_index('ix_care_gaps_patient', 'care_gaps', ['patient_id'])
    op.create_index('ix_care_gaps_status', 'care_gaps', ['status'])
    op.create_index('ix_care_gaps_priority', 'care_gaps', ['priority'])
    op.create_index('ix_care_gaps_provider', 'care_gaps', ['attributed_provider_id'])
    op.create_index('ix_care_gaps_due_date', 'care_gaps', ['due_date'])

    # Chronic Disease Registries - Disease registry tracking
    op.create_table(
        'chronic_disease_registries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Condition
        sa.Column('condition', sa.Enum('diabetes', 'hypertension', 'heart_failure', 'copd', 'asthma',
                                        'ckd', 'depression', 'obesity', 'cancer', 'stroke',
                                        name='chronic_condition'), nullable=False),
        sa.Column('condition_onset_date', sa.Date, nullable=True),
        sa.Column('condition_stage', sa.String(50), nullable=True),

        # Status
        sa.Column('registry_status', sa.String(50), nullable=False, default='active'),
        sa.Column('is_controlled', sa.Boolean, nullable=True),
        sa.Column('control_status', sa.String(50), nullable=True),  # Controlled, Uncontrolled, Improving

        # Clinical indicators
        sa.Column('latest_indicators', postgresql.JSONB, default={}),  # A1c, BP, eGFR, etc.
        sa.Column('indicator_history', postgresql.JSONB, default=[]),

        # Management
        sa.Column('current_medications', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('care_plan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_visit_date', sa.Date, nullable=True),
        sa.Column('next_scheduled_visit', sa.Date, nullable=True),

        # Care gaps for this condition
        sa.Column('open_care_gaps', sa.Integer, default=0),
        sa.Column('care_gap_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),

        # Risk
        sa.Column('condition_risk_score', sa.Float, nullable=True),
        sa.Column('complication_risk', sa.String(20), nullable=True),

        # Attribution
        sa.Column('primary_provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('specialist_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('enrolled_date', sa.Date, nullable=False),
        sa.Column('disenrolled_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_registries_tenant', 'chronic_disease_registries', ['tenant_id'])
    op.create_index('ix_registries_patient', 'chronic_disease_registries', ['patient_id'])
    op.create_index('ix_registries_condition', 'chronic_disease_registries', ['condition'])
    op.create_index('ix_registries_status', 'chronic_disease_registries', ['registry_status'])
    op.create_index('ix_registries_controlled', 'chronic_disease_registries', ['is_controlled'])
    op.create_unique_constraint('uq_registry_patient_condition', 'chronic_disease_registries',
                                ['tenant_id', 'patient_id', 'condition'])

    # SDOH Assessments - Social determinants assessments
    op.create_table(
        'sdoh_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Assessment
        sa.Column('assessment_date', sa.Date, nullable=False),
        sa.Column('assessment_tool', sa.String(100), nullable=True),  # PRAPARE, AHC HRSN, etc.
        sa.Column('assessed_by', postgresql.UUID(as_uuid=True), nullable=True),

        # SDOH domains
        sa.Column('housing_instability', sa.Boolean, default=False),
        sa.Column('housing_details', postgresql.JSONB, default={}),

        sa.Column('food_insecurity', sa.Boolean, default=False),
        sa.Column('food_details', postgresql.JSONB, default={}),

        sa.Column('transportation_barriers', sa.Boolean, default=False),
        sa.Column('transportation_details', postgresql.JSONB, default={}),

        sa.Column('utility_difficulty', sa.Boolean, default=False),
        sa.Column('utility_details', postgresql.JSONB, default={}),

        sa.Column('interpersonal_safety', sa.Boolean, default=False),
        sa.Column('safety_details', postgresql.JSONB, default={}),

        sa.Column('financial_strain', sa.Boolean, default=False),
        sa.Column('financial_details', postgresql.JSONB, default={}),

        sa.Column('social_isolation', sa.Boolean, default=False),
        sa.Column('social_details', postgresql.JSONB, default={}),

        sa.Column('education_barriers', sa.Boolean, default=False),
        sa.Column('education_details', postgresql.JSONB, default={}),

        sa.Column('employment_barriers', sa.Boolean, default=False),
        sa.Column('employment_details', postgresql.JSONB, default={}),

        # Summary
        sa.Column('total_needs_identified', sa.Integer, default=0),
        sa.Column('z_codes', postgresql.ARRAY(sa.String), default=[]),  # ICD-10 Z codes
        sa.Column('sdoh_risk_score', sa.Float, nullable=True),

        # Interventions
        sa.Column('referrals_made', postgresql.JSONB, default=[]),
        sa.Column('resources_provided', postgresql.JSONB, default=[]),
        sa.Column('follow_up_date', sa.Date, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_sdoh_tenant', 'sdoh_assessments', ['tenant_id'])
    op.create_index('ix_sdoh_patient', 'sdoh_assessments', ['patient_id'])
    op.create_index('ix_sdoh_date', 'sdoh_assessments', ['assessment_date'])
    op.create_index('ix_sdoh_needs', 'sdoh_assessments', ['total_needs_identified'])

    # Revenue Snapshots - Financial performance snapshots
    op.create_table(
        'revenue_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Period
        sa.Column('snapshot_date', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),  # Daily, Weekly, Monthly
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),

        # Gross revenue
        sa.Column('gross_charges', sa.Float, default=0),
        sa.Column('gross_revenue', sa.Float, default=0),

        # Adjustments
        sa.Column('contractual_adjustments', sa.Float, default=0),
        sa.Column('bad_debt', sa.Float, default=0),
        sa.Column('charity_care', sa.Float, default=0),
        sa.Column('other_adjustments', sa.Float, default=0),

        # Net revenue
        sa.Column('net_revenue', sa.Float, default=0),
        sa.Column('net_collection_rate', sa.Float, nullable=True),

        # Collections
        sa.Column('total_collections', sa.Float, default=0),
        sa.Column('insurance_collections', sa.Float, default=0),
        sa.Column('patient_collections', sa.Float, default=0),

        # By service line
        sa.Column('revenue_by_service_line', postgresql.JSONB, default={}),

        # By payer
        sa.Column('revenue_by_payer', postgresql.JSONB, default={}),

        # Volume
        sa.Column('total_encounters', sa.Integer, default=0),
        sa.Column('total_rvu', sa.Float, default=0),
        sa.Column('revenue_per_encounter', sa.Float, nullable=True),
        sa.Column('revenue_per_rvu', sa.Float, nullable=True),

        # Trends
        sa.Column('prior_period_revenue', sa.Float, nullable=True),
        sa.Column('revenue_change_pct', sa.Float, nullable=True),
        sa.Column('trend', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                   name='metric_trend'), nullable=True),

        # Benchmarks
        sa.Column('budget_amount', sa.Float, nullable=True),
        sa.Column('variance_from_budget', sa.Float, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_revenue_tenant', 'revenue_snapshots', ['tenant_id'])
    op.create_index('ix_revenue_date', 'revenue_snapshots', ['snapshot_date'])
    op.create_index('ix_revenue_period', 'revenue_snapshots', ['period_start', 'period_end'])
    op.create_unique_constraint('uq_revenue_snapshot', 'revenue_snapshots', ['tenant_id', 'snapshot_date', 'period_type'])

    # Denial Records - Claims denial tracking
    op.create_table(
        'denial_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Claim reference
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_number', sa.String(50), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Denial info
        sa.Column('denial_date', sa.Date, nullable=False),
        sa.Column('denial_reason', sa.Enum('eligibility', 'authorization', 'coding_error', 'medical_necessity',
                                            'duplicate', 'timely_filing', 'missing_info', 'bundling',
                                            'modifier', 'coordination_benefits', 'out_of_network', 'other',
                                            name='denial_reason'), nullable=False),
        sa.Column('denial_reason_detail', sa.Text, nullable=True),
        sa.Column('rarc_code', sa.String(20), nullable=True),
        sa.Column('carc_code', sa.String(20), nullable=True),

        # Amounts
        sa.Column('denied_amount', sa.Float, nullable=False),
        sa.Column('total_claim_amount', sa.Float, nullable=True),

        # Payer
        sa.Column('payer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payer_name', sa.String(200), nullable=True),
        sa.Column('payer_type', sa.Enum('medicare', 'medicaid', 'commercial', 'self_pay',
                                        'workers_comp', 'tricare', 'va', 'other_government',
                                        'no_fault', 'uninsured', name='payer_type'), nullable=True),

        # Status
        sa.Column('status', sa.String(50), nullable=False, default='denied'),  # Denied, Appealed, Overturned, Written Off
        sa.Column('is_appealable', sa.Boolean, default=True),

        # Appeal
        sa.Column('appeal_date', sa.Date, nullable=True),
        sa.Column('appeal_outcome', sa.String(50), nullable=True),
        sa.Column('recovered_amount', sa.Float, default=0),

        # Root cause
        sa.Column('root_cause', sa.String(100), nullable=True),
        sa.Column('responsible_department', sa.String(100), nullable=True),
        sa.Column('preventable', sa.Boolean, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_denials_tenant', 'denial_records', ['tenant_id'])
    op.create_index('ix_denials_claim', 'denial_records', ['claim_id'])
    op.create_index('ix_denials_date', 'denial_records', ['denial_date'])
    op.create_index('ix_denials_reason', 'denial_records', ['denial_reason'])
    op.create_index('ix_denials_payer', 'denial_records', ['payer_id'])
    op.create_index('ix_denials_status', 'denial_records', ['status'])

    # AR Aging Snapshots - AR aging history
    op.create_table(
        'ar_aging_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Period
        sa.Column('snapshot_date', sa.Date, nullable=False),

        # Total AR
        sa.Column('total_ar', sa.Float, nullable=False),
        sa.Column('total_claims', sa.Integer, default=0),

        # By aging bucket
        sa.Column('ar_current', sa.Float, default=0),  # 0-30 days
        sa.Column('ar_31_60', sa.Float, default=0),
        sa.Column('ar_61_90', sa.Float, default=0),
        sa.Column('ar_91_120', sa.Float, default=0),
        sa.Column('ar_over_120', sa.Float, default=0),

        # Percentages
        sa.Column('pct_current', sa.Float, nullable=True),
        sa.Column('pct_31_60', sa.Float, nullable=True),
        sa.Column('pct_61_90', sa.Float, nullable=True),
        sa.Column('pct_91_120', sa.Float, nullable=True),
        sa.Column('pct_over_120', sa.Float, nullable=True),

        # By payer type
        sa.Column('ar_by_payer_type', postgresql.JSONB, default={}),

        # Metrics
        sa.Column('days_in_ar', sa.Float, nullable=True),
        sa.Column('average_age', sa.Float, nullable=True),
        sa.Column('collection_probability', sa.Float, nullable=True),
        sa.Column('expected_collection', sa.Float, nullable=True),

        # Trends
        sa.Column('prior_ar', sa.Float, nullable=True),
        sa.Column('ar_change', sa.Float, nullable=True),
        sa.Column('trend', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                   name='metric_trend'), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_ar_aging_tenant', 'ar_aging_snapshots', ['tenant_id'])
    op.create_index('ix_ar_aging_date', 'ar_aging_snapshots', ['snapshot_date'])
    op.create_unique_constraint('uq_ar_aging_snapshot', 'ar_aging_snapshots', ['tenant_id', 'snapshot_date'])

    # Department Productivity - Operational metrics
    op.create_table(
        'department_productivity',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Department
        sa.Column('department_type', sa.Enum('emergency', 'inpatient', 'outpatient', 'surgery', 'radiology',
                                              'laboratory', 'pharmacy', 'rehabilitation', 'behavioral_health', 'primary_care',
                                              name='department_type'), nullable=False),
        sa.Column('department_name', sa.String(200), nullable=True),

        # Period
        sa.Column('measurement_date', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),

        # Volume
        sa.Column('total_encounters', sa.Integer, default=0),
        sa.Column('total_procedures', sa.Integer, default=0),
        sa.Column('total_rvu', sa.Float, default=0),

        # Staffing
        sa.Column('total_fte', sa.Float, nullable=True),
        sa.Column('productive_hours', sa.Float, nullable=True),
        sa.Column('non_productive_hours', sa.Float, nullable=True),

        # Productivity
        sa.Column('encounters_per_fte', sa.Float, nullable=True),
        sa.Column('rvu_per_fte', sa.Float, nullable=True),
        sa.Column('revenue_per_fte', sa.Float, nullable=True),

        # Financial
        sa.Column('total_revenue', sa.Float, default=0),
        sa.Column('total_cost', sa.Float, default=0),
        sa.Column('contribution_margin', sa.Float, nullable=True),
        sa.Column('cost_per_encounter', sa.Float, nullable=True),

        # Benchmarks
        sa.Column('benchmark_rvu_per_fte', sa.Float, nullable=True),
        sa.Column('variance_from_benchmark', sa.Float, nullable=True),

        # Trends
        sa.Column('prior_productivity', sa.Float, nullable=True),
        sa.Column('trend', sa.Enum('improving', 'declining', 'stable', 'volatile',
                                   name='metric_trend'), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_dept_productivity_tenant', 'department_productivity', ['tenant_id'])
    op.create_index('ix_dept_productivity_dept', 'department_productivity', ['department_type'])
    op.create_index('ix_dept_productivity_date', 'department_productivity', ['measurement_date'])
    op.create_index('ix_dept_productivity_facility', 'department_productivity', ['facility_id'])

    # Resource Utilization - Resource usage tracking
    op.create_table(
        'resource_utilization',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Resource
        sa.Column('resource_type', sa.Enum('bed', 'or_room', 'exam_room', 'imaging_equipment', 'ventilator',
                                            'infusion_pump', 'wheelchair', 'stretcher', 'isolation_room', 'icu_bed',
                                            name='resource_type'), nullable=False),
        sa.Column('resource_name', sa.String(200), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),

        # Period
        sa.Column('measurement_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_minutes', sa.Integer, default=60),  # Granularity: 15, 30, 60 min

        # Capacity
        sa.Column('total_available', sa.Integer, nullable=False),
        sa.Column('total_in_use', sa.Integer, nullable=False),
        sa.Column('total_blocked', sa.Integer, default=0),  # Maintenance, cleaning, etc.

        # Utilization
        sa.Column('utilization_rate', sa.Float, nullable=False),
        sa.Column('peak_utilization', sa.Float, nullable=True),
        sa.Column('min_utilization', sa.Float, nullable=True),

        # Turnover (for beds, ORs)
        sa.Column('turnover_count', sa.Integer, default=0),
        sa.Column('avg_turnover_time_minutes', sa.Float, nullable=True),

        # Wait times
        sa.Column('patients_waiting', sa.Integer, default=0),
        sa.Column('avg_wait_time_minutes', sa.Float, nullable=True),

        # Benchmarks
        sa.Column('target_utilization', sa.Float, nullable=True),
        sa.Column('variance_from_target', sa.Float, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_resource_util_tenant', 'resource_utilization', ['tenant_id'])
    op.create_index('ix_resource_util_type', 'resource_utilization', ['resource_type'])
    op.create_index('ix_resource_util_datetime', 'resource_utilization', ['measurement_datetime'])
    op.create_index('ix_resource_util_facility', 'resource_utilization', ['facility_id'])

    # Patient Flow Events - Patient flow tracking
    op.create_table(
        'patient_flow_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Event
        sa.Column('event_type', sa.String(50), nullable=False),  # Arrival, Triage, Roomed, Provider, Disposition, Discharge
        sa.Column('event_datetime', sa.DateTime(timezone=True), nullable=False),

        # Location
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('bed', sa.String(50), nullable=True),

        # Staff
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('staff_role', sa.String(50), nullable=True),

        # Timing
        sa.Column('time_since_arrival_minutes', sa.Float, nullable=True),
        sa.Column('time_since_previous_event_minutes', sa.Float, nullable=True),

        # Status at event
        sa.Column('acuity_level', sa.SmallInteger, nullable=True),  # ESI 1-5
        sa.Column('chief_complaint', sa.String(500), nullable=True),

        # Notes
        sa.Column('notes', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_patient_flow_tenant', 'patient_flow_events', ['tenant_id'])
    op.create_index('ix_patient_flow_encounter', 'patient_flow_events', ['encounter_id'])
    op.create_index('ix_patient_flow_datetime', 'patient_flow_events', ['event_datetime'])
    op.create_index('ix_patient_flow_type', 'patient_flow_events', ['event_type'])
    op.create_index('ix_patient_flow_facility', 'patient_flow_events', ['facility_id'])

    # ML Models - Predictive model registry
    op.create_table(
        'ml_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Model identification
        sa.Column('model_id', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(200), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('model_type', sa.Enum('readmission', 'length_of_stay', 'no_show', 'deterioration',
                                         'cost', 'mortality', 'sepsis', 'fall_risk', 'icu_transfer', 'custom',
                                         name='ml_model_type'), nullable=False),

        # Description
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('use_case', sa.Text, nullable=True),

        # Algorithm
        sa.Column('algorithm', sa.String(100), nullable=True),  # XGBoost, LightGBM, Neural Network, etc.
        sa.Column('framework', sa.String(50), nullable=True),  # sklearn, tensorflow, pytorch
        sa.Column('hyperparameters', postgresql.JSONB, default={}),

        # Features
        sa.Column('feature_count', sa.Integer, nullable=True),
        sa.Column('feature_names', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('feature_importance', postgresql.JSONB, default={}),

        # Training
        sa.Column('training_data_start', sa.Date, nullable=True),
        sa.Column('training_data_end', sa.Date, nullable=True),
        sa.Column('training_sample_size', sa.Integer, nullable=True),
        sa.Column('training_date', sa.DateTime(timezone=True), nullable=True),

        # Performance metrics
        sa.Column('auc_roc', sa.Float, nullable=True),
        sa.Column('accuracy', sa.Float, nullable=True),
        sa.Column('precision', sa.Float, nullable=True),
        sa.Column('recall', sa.Float, nullable=True),
        sa.Column('f1_score', sa.Float, nullable=True),
        sa.Column('calibration_error', sa.Float, nullable=True),
        sa.Column('additional_metrics', postgresql.JSONB, default={}),

        # Thresholds
        sa.Column('classification_threshold', sa.Float, default=0.5),
        sa.Column('risk_thresholds', postgresql.JSONB, default={}),

        # Status
        sa.Column('status', sa.Enum('development', 'validation', 'staging', 'production', 'deprecated', 'archived',
                                     name='ml_model_status'), nullable=False, default='development'),
        sa.Column('deployed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_date', sa.DateTime(timezone=True), nullable=True),

        # Artifact
        sa.Column('artifact_path', sa.String(500), nullable=True),
        sa.Column('artifact_hash', sa.String(64), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_ml_models_tenant', 'ml_models', ['tenant_id'])
    op.create_index('ix_ml_models_model_id', 'ml_models', ['model_id'])
    op.create_index('ix_ml_models_type', 'ml_models', ['model_type'])
    op.create_index('ix_ml_models_status', 'ml_models', ['status'])
    op.create_unique_constraint('uq_ml_model_version', 'ml_models', ['tenant_id', 'model_id', 'model_version'])

    # ML Predictions - Prediction results
    op.create_table(
        'ml_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # References
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Prediction
        sa.Column('prediction_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('prediction_type', sa.String(50), nullable=False),

        # Results
        sa.Column('probability', sa.Float, nullable=False),
        sa.Column('predicted_class', sa.String(50), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),

        # For regression models
        sa.Column('predicted_value', sa.Float, nullable=True),
        sa.Column('prediction_lower', sa.Float, nullable=True),
        sa.Column('prediction_upper', sa.Float, nullable=True),

        # Explainability
        sa.Column('feature_contributions', postgresql.JSONB, default={}),
        sa.Column('top_factors', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('explanation_text', sa.Text, nullable=True),

        # Input snapshot
        sa.Column('input_features', postgresql.JSONB, default={}),

        # Outcome tracking
        sa.Column('actual_outcome', sa.String(50), nullable=True),
        sa.Column('actual_value', sa.Float, nullable=True),
        sa.Column('outcome_date', sa.Date, nullable=True),
        sa.Column('prediction_correct', sa.Boolean, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_predictions_tenant', 'ml_predictions', ['tenant_id'])
    op.create_index('ix_predictions_model', 'ml_predictions', ['model_id'])
    op.create_index('ix_predictions_patient', 'ml_predictions', ['patient_id'])
    op.create_index('ix_predictions_encounter', 'ml_predictions', ['encounter_id'])
    op.create_index('ix_predictions_datetime', 'ml_predictions', ['prediction_datetime'])
    op.create_index('ix_predictions_risk', 'ml_predictions', ['risk_level'])

    # Model Drift Metrics - Model monitoring
    op.create_table(
        'model_drift_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Period
        sa.Column('measurement_date', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),

        # Data drift
        sa.Column('data_drift_detected', sa.Boolean, default=False),
        sa.Column('psi_score', sa.Float, nullable=True),  # Population Stability Index
        sa.Column('feature_drift_scores', postgresql.JSONB, default={}),
        sa.Column('drifted_features', postgresql.ARRAY(sa.String), default=[]),

        # Concept drift
        sa.Column('concept_drift_detected', sa.Boolean, default=False),
        sa.Column('performance_degradation', sa.Float, nullable=True),

        # Current performance
        sa.Column('current_auc', sa.Float, nullable=True),
        sa.Column('current_accuracy', sa.Float, nullable=True),
        sa.Column('current_precision', sa.Float, nullable=True),
        sa.Column('current_recall', sa.Float, nullable=True),
        sa.Column('calibration_error', sa.Float, nullable=True),

        # Baseline comparison
        sa.Column('baseline_auc', sa.Float, nullable=True),
        sa.Column('auc_change', sa.Float, nullable=True),

        # Predictions summary
        sa.Column('prediction_count', sa.Integer, default=0),
        sa.Column('avg_probability', sa.Float, nullable=True),
        sa.Column('probability_distribution', postgresql.JSONB, default={}),

        # Alerts
        sa.Column('alert_level', sa.String(20), nullable=True),  # None, Warning, Critical
        sa.Column('alert_message', sa.Text, nullable=True),
        sa.Column('requires_retraining', sa.Boolean, default=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_drift_tenant', 'model_drift_metrics', ['tenant_id'])
    op.create_index('ix_drift_model', 'model_drift_metrics', ['model_id'])
    op.create_index('ix_drift_date', 'model_drift_metrics', ['measurement_date'])
    op.create_index('ix_drift_alert', 'model_drift_metrics', ['alert_level'])
    op.create_unique_constraint('uq_drift_metric', 'model_drift_metrics', ['tenant_id', 'model_id', 'measurement_date'])

    # AB Test Results - Model A/B tests
    op.create_table(
        'ab_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Test configuration
        sa.Column('test_name', sa.String(200), nullable=False),
        sa.Column('test_description', sa.Text, nullable=True),
        sa.Column('model_a_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_b_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Test period
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='running'),

        # Sample sizes
        sa.Column('sample_size_a', sa.Integer, default=0),
        sa.Column('sample_size_b', sa.Integer, default=0),
        sa.Column('traffic_split', sa.Float, default=0.5),

        # Model A metrics
        sa.Column('auc_a', sa.Float, nullable=True),
        sa.Column('accuracy_a', sa.Float, nullable=True),
        sa.Column('precision_a', sa.Float, nullable=True),
        sa.Column('recall_a', sa.Float, nullable=True),

        # Model B metrics
        sa.Column('auc_b', sa.Float, nullable=True),
        sa.Column('accuracy_b', sa.Float, nullable=True),
        sa.Column('precision_b', sa.Float, nullable=True),
        sa.Column('recall_b', sa.Float, nullable=True),

        # Statistical analysis
        sa.Column('auc_difference', sa.Float, nullable=True),
        sa.Column('p_value', sa.Float, nullable=True),
        sa.Column('confidence_interval_lower', sa.Float, nullable=True),
        sa.Column('confidence_interval_upper', sa.Float, nullable=True),
        sa.Column('is_significant', sa.Boolean, nullable=True),

        # Recommendation
        sa.Column('winner', sa.String(1), nullable=True),  # 'A', 'B', or None
        sa.Column('recommendation', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_ab_tests_tenant', 'ab_test_results', ['tenant_id'])
    op.create_index('ix_ab_tests_models', 'ab_test_results', ['model_a_id', 'model_b_id'])
    op.create_index('ix_ab_tests_status', 'ab_test_results', ['status'])

    # Report Definitions - Custom report configs
    op.create_table(
        'report_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Report info
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('report_type', sa.Enum('dashboard', 'tabular', 'summary', 'detail', 'trending', 'comparison', 'scorecard',
                                          name='report_type'), nullable=False),

        # Data source
        sa.Column('data_source', sa.String(100), nullable=False),
        sa.Column('data_query', postgresql.JSONB, default={}),
        sa.Column('custom_sql', sa.Text, nullable=True),

        # Columns and metrics
        sa.Column('columns', postgresql.JSONB, default=[]),
        sa.Column('metrics', postgresql.JSONB, default=[]),
        sa.Column('calculated_fields', postgresql.JSONB, default=[]),

        # Filters
        sa.Column('filters', postgresql.JSONB, default=[]),
        sa.Column('default_filters', postgresql.JSONB, default={}),
        sa.Column('user_filters', postgresql.JSONB, default=[]),

        # Grouping and sorting
        sa.Column('group_by', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('sort_by', postgresql.JSONB, default=[]),

        # Visualization
        sa.Column('visualizations', postgresql.JSONB, default=[]),
        sa.Column('default_visualization', sa.Enum('bar_chart', 'line_chart', 'pie_chart', 'donut_chart', 'area_chart',
                                                    'scatter_plot', 'heat_map', 'treemap', 'funnel', 'gauge',
                                                    'table', 'pivot_table', 'kpi_card', 'sparkline', 'waterfall',
                                                    'sankey', 'bullet_chart', 'radar_chart', 'box_plot', 'histogram',
                                                    name='visualization_type'), nullable=True),

        # Export settings
        sa.Column('export_formats', postgresql.ARRAY(sa.String), default=['pdf', 'excel', 'csv']),
        sa.Column('export_settings', postgresql.JSONB, default={}),

        # Sharing
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('shared_with_roles', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('shared_with_users', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_template', sa.Boolean, default=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_report_defs_tenant', 'report_definitions', ['tenant_id'])
    op.create_index('ix_report_defs_creator', 'report_definitions', ['created_by'])
    op.create_index('ix_report_defs_type', 'report_definitions', ['report_type'])
    op.create_index('ix_report_defs_template', 'report_definitions', ['is_template'])

    # Report Executions - Report run history
    op.create_table(
        'report_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('executed_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Execution
        sa.Column('execution_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('execution_type', sa.String(50), nullable=False, default='manual'),  # Manual, Scheduled, API

        # Parameters
        sa.Column('parameters', postgresql.JSONB, default={}),
        sa.Column('filters_applied', postgresql.JSONB, default={}),

        # Results
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('execution_time_ms', sa.Float, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='running'),  # Running, Completed, Failed

        # Output
        sa.Column('output_format', sa.Enum('pdf', 'excel', 'csv', 'powerpoint', 'json', 'xml', 'png', 'html',
                                            name='export_format'), nullable=True),
        sa.Column('output_path', sa.String(500), nullable=True),
        sa.Column('output_size_bytes', sa.BigInteger, nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', postgresql.JSONB, default={}),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_report_exec_tenant', 'report_executions', ['tenant_id'])
    op.create_index('ix_report_exec_report', 'report_executions', ['report_id'])
    op.create_index('ix_report_exec_datetime', 'report_executions', ['execution_datetime'])
    op.create_index('ix_report_exec_status', 'report_executions', ['status'])

    # Scheduled Reports - Report scheduling
    op.create_table(
        'scheduled_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Schedule
        sa.Column('schedule_name', sa.String(200), nullable=False),
        sa.Column('frequency', sa.Enum('once', 'daily', 'weekly', 'biweekly', 'monthly', 'quarterly', 'annually',
                                        name='schedule_frequency'), nullable=False),
        sa.Column('schedule_config', postgresql.JSONB, default={}),  # Day of week, day of month, time, etc.
        sa.Column('timezone', sa.String(50), default='UTC'),

        # Next run
        sa.Column('next_run_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_datetime', sa.DateTime(timezone=True), nullable=True),

        # Parameters
        sa.Column('parameters', postgresql.JSONB, default={}),
        sa.Column('output_format', sa.Enum('pdf', 'excel', 'csv', 'powerpoint', 'json', 'xml', 'png', 'html',
                                            name='export_format'), nullable=False),

        # Distribution
        sa.Column('recipients', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('distribution_list_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email_subject', sa.String(500), nullable=True),
        sa.Column('email_body', sa.Text, nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('consecutive_failures', sa.Integer, default=0),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_sched_reports_tenant', 'scheduled_reports', ['tenant_id'])
    op.create_index('ix_sched_reports_report', 'scheduled_reports', ['report_id'])
    op.create_index('ix_sched_reports_next_run', 'scheduled_reports', ['next_run_datetime'])
    op.create_index('ix_sched_reports_active', 'scheduled_reports', ['is_active'])

    # Report Templates - Reusable templates
    op.create_table(
        'report_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),  # Null for system templates

        # Template info
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),  # Financial, Clinical, Operational, etc.
        sa.Column('report_type', sa.Enum('dashboard', 'tabular', 'summary', 'detail', 'trending', 'comparison', 'scorecard',
                                          name='report_type'), nullable=False),

        # Template definition
        sa.Column('template_config', postgresql.JSONB, nullable=False),
        sa.Column('default_columns', postgresql.JSONB, default=[]),
        sa.Column('default_metrics', postgresql.JSONB, default=[]),
        sa.Column('default_filters', postgresql.JSONB, default=[]),
        sa.Column('default_visualizations', postgresql.JSONB, default=[]),

        # Requirements
        sa.Column('required_data_sources', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('required_permissions', postgresql.ARRAY(sa.String), default=[]),

        # Metadata
        sa.Column('is_system_template', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('version', sa.String(20), default='1.0'),

        # Usage tracking
        sa.Column('usage_count', sa.Integer, default=0),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_report_templates_tenant', 'report_templates', ['tenant_id'])
    op.create_index('ix_report_templates_category', 'report_templates', ['category'])
    op.create_index('ix_report_templates_type', 'report_templates', ['report_type'])
    op.create_index('ix_report_templates_system', 'report_templates', ['is_system_template'])

    # Analytics Audit Log - Analytics access logging
    op.create_table(
        'analytics_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Action
        sa.Column('action_type', sa.String(50), nullable=False),  # View, Export, Create, Update, Delete
        sa.Column('resource_type', sa.String(50), nullable=False),  # Dashboard, Report, Model, etc.
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_name', sa.String(200), nullable=True),

        # Details
        sa.Column('action_details', postgresql.JSONB, default={}),
        sa.Column('parameters', postgresql.JSONB, default={}),

        # Context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),

        # Results
        sa.Column('status', sa.String(20), nullable=False, default='success'),  # Success, Failed, Denied
        sa.Column('error_message', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_analytics_audit_tenant', 'analytics_audit_log', ['tenant_id'])
    op.create_index('ix_analytics_audit_user', 'analytics_audit_log', ['user_id'])
    op.create_index('ix_analytics_audit_action', 'analytics_audit_log', ['action_type'])
    op.create_index('ix_analytics_audit_resource', 'analytics_audit_log', ['resource_type', 'resource_id'])
    op.create_index('ix_analytics_audit_created', 'analytics_audit_log', ['created_at'])

    # Analytics Statistics - Usage tracking
    op.create_table(
        'analytics_statistics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stats_date', sa.Date, nullable=False),

        # Dashboard usage
        sa.Column('dashboard_views', sa.Integer, default=0),
        sa.Column('unique_dashboard_users', sa.Integer, default=0),

        # Report usage
        sa.Column('reports_generated', sa.Integer, default=0),
        sa.Column('reports_exported', sa.Integer, default=0),
        sa.Column('scheduled_reports_run', sa.Integer, default=0),

        # Prediction usage
        sa.Column('predictions_made', sa.Integer, default=0),
        sa.Column('high_risk_predictions', sa.Integer, default=0),

        # Query metrics
        sa.Column('queries_executed', sa.Integer, default=0),
        sa.Column('avg_query_time_ms', sa.Float, default=0),

        # Data freshness
        sa.Column('last_etl_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_lag_hours', sa.Float, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_analytics_stats_tenant', 'analytics_statistics', ['tenant_id'])
    op.create_index('ix_analytics_stats_date', 'analytics_statistics', ['stats_date'])
    op.create_unique_constraint('uq_analytics_stats', 'analytics_statistics', ['tenant_id', 'stats_date'])


def downgrade() -> None:
    # Drop operational tables in reverse order
    op.drop_table('analytics_statistics')
    op.drop_table('analytics_audit_log')
    op.drop_table('report_templates')
    op.drop_table('scheduled_reports')
    op.drop_table('report_executions')
    op.drop_table('report_definitions')
    op.drop_table('ab_test_results')
    op.drop_table('model_drift_metrics')
    op.drop_table('ml_predictions')
    op.drop_table('ml_models')
    op.drop_table('patient_flow_events')
    op.drop_table('resource_utilization')
    op.drop_table('department_productivity')
    op.drop_table('ar_aging_snapshots')
    op.drop_table('denial_records')
    op.drop_table('revenue_snapshots')
    op.drop_table('sdoh_assessments')
    op.drop_table('chronic_disease_registries')
    op.drop_table('care_gaps')
    op.drop_table('patient_risk_profiles')
    op.drop_table('provider_scorecards')
    op.drop_table('quality_measures')
    op.drop_table('kpi_snapshots')
    op.drop_table('executive_dashboards')

    # Drop fact tables
    op.drop_table('fact_quality_measures')
    op.drop_table('fact_encounters')

    # Drop dimension tables
    op.drop_table('dim_payers')
    op.drop_table('dim_procedures')
    op.drop_table('dim_diagnoses')
    op.drop_table('dim_facilities')
    op.drop_table('dim_providers')
    op.drop_table('dim_patients')
    op.drop_table('dim_time')
    op.drop_table('dim_date')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS schedule_frequency')
    op.execute('DROP TYPE IF EXISTS export_format')
    op.execute('DROP TYPE IF EXISTS visualization_type')
    op.execute('DROP TYPE IF EXISTS report_type')
    op.execute('DROP TYPE IF EXISTS ml_model_status')
    op.execute('DROP TYPE IF EXISTS ml_model_type')
    op.execute('DROP TYPE IF EXISTS resource_type')
    op.execute('DROP TYPE IF EXISTS department_type')
    op.execute('DROP TYPE IF EXISTS ar_aging_bucket')
    op.execute('DROP TYPE IF EXISTS denial_reason')
    op.execute('DROP TYPE IF EXISTS payer_type')
    op.execute('DROP TYPE IF EXISTS chronic_condition')
    op.execute('DROP TYPE IF EXISTS care_gap_status')
    op.execute('DROP TYPE IF EXISTS care_gap_priority')
    op.execute('DROP TYPE IF EXISTS performance_status')
    op.execute('DROP TYPE IF EXISTS measure_program')
    op.execute('DROP TYPE IF EXISTS measure_category')
    op.execute('DROP TYPE IF EXISTS performance_level')
    op.execute('DROP TYPE IF EXISTS metric_trend')
