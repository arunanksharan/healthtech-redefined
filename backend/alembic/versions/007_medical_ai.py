"""Medical AI Tables

Revision ID: 007_medical_ai
Revises: 006_ai_platform
Create Date: 2024-11-25

EPIC-010: Medical AI Capabilities

Tables:
- medical_triage_results: AI triage assessments with explainability
- clinical_documentation: SOAP notes and clinical documentation
- entity_extractions: Medical entity extraction results
- clinical_decisions: Clinical decision support logs
- predictive_analytics: Risk predictions and scoring
- image_analyses: Medical image analysis results
- nlp_pipeline_results: Clinical NLP processing results
- voice_biomarker_analyses: Voice biomarker analysis results
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '007_medical_ai'
down_revision = '006_ai_platform'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Enums ====================

    # Urgency Level
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE urgency_level AS ENUM (
                'emergency', 'urgent', 'less_urgent', 'semi_urgent',
                'non_urgent', 'self_care'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Risk Level
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_level AS ENUM (
                'very_low', 'low', 'moderate', 'high', 'very_high', 'critical'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Medical Entity Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medical_entity_type AS ENUM (
                'condition', 'medication', 'procedure', 'anatomy',
                'laboratory', 'vital_sign', 'symptom', 'device'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Negation Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE negation_status AS ENUM (
                'affirmed', 'negated', 'uncertain', 'hypothetical',
                'family_history', 'historical'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Interaction Severity
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE interaction_severity AS ENUM (
                'minor', 'moderate', 'major', 'contraindicated'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Documentation Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentation_type AS ENUM (
                'soap_note', 'progress_note', 'discharge_summary',
                'consultation', 'operative_note', 'h_and_p'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Image Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medical_image_type AS ENUM (
                'chest_xray', 'skin_lesion', 'wound', 'ct_scan', 'mri'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==================== Medical Triage Results ====================

    op.create_table(
        'medical_triage_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Input data
        sa.Column('chief_complaint', sa.Text, nullable=False),
        sa.Column('symptoms', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('patient_age', sa.Integer, nullable=True),
        sa.Column('patient_gender', sa.String(20), nullable=True),
        sa.Column('vital_signs', postgresql.JSONB, default={}),
        sa.Column('medical_history', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('current_medications', postgresql.ARRAY(sa.String), default=[]),

        # Triage results
        sa.Column('urgency_level', sa.Enum('emergency', 'urgent', 'less_urgent',
                                           'semi_urgent', 'non_urgent', 'self_care',
                                           name='urgency_level'), nullable=False),
        sa.Column('esi_level', sa.Integer, nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('recommended_department', sa.String(100), nullable=False),

        # Red flags
        sa.Column('red_flags', postgresql.JSONB, default=[]),
        sa.Column('red_flag_count', sa.Integer, default=0),

        # Symptom analysis
        sa.Column('symptom_analysis', postgresql.JSONB, default={}),

        # Explainability
        sa.Column('explanation', postgresql.JSONB, default={}),
        sa.Column('decision_path', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('suggested_questions', postgresql.ARRAY(sa.String), default=[]),

        # Metadata
        sa.Column('estimated_wait_time', sa.String(50), nullable=True),
        sa.Column('model_version', sa.String(50), default='triage-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_triage_results_tenant_id', 'medical_triage_results', ['tenant_id'])
    op.create_index('ix_triage_results_patient_id', 'medical_triage_results', ['patient_id'])
    op.create_index('ix_triage_results_urgency', 'medical_triage_results', ['urgency_level'])
    op.create_index('ix_triage_results_created', 'medical_triage_results', ['created_at'])

    # ==================== Clinical Documentation ====================

    op.create_table(
        'clinical_documentation',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Documentation type
        sa.Column('documentation_type', sa.Enum('soap_note', 'progress_note', 'discharge_summary',
                                                 'consultation', 'operative_note', 'h_and_p',
                                                 name='documentation_type'), nullable=False),

        # Source
        sa.Column('source_transcript', sa.Text, nullable=True),
        sa.Column('transcription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_notes', sa.Text, nullable=True),

        # SOAP sections
        sa.Column('subjective', sa.Text, nullable=True),
        sa.Column('objective', sa.Text, nullable=True),
        sa.Column('assessment', sa.Text, nullable=True),
        sa.Column('plan', sa.Text, nullable=True),

        # Coding suggestions
        sa.Column('icd10_codes', postgresql.JSONB, default=[]),
        sa.Column('cpt_codes', postgresql.JSONB, default=[]),
        sa.Column('hcc_codes', postgresql.JSONB, default=[]),

        # Status
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),

        # Metadata
        sa.Column('model_version', sa.String(50), default='doc-ai-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_clinical_docs_tenant_id', 'clinical_documentation', ['tenant_id'])
    op.create_index('ix_clinical_docs_patient_id', 'clinical_documentation', ['patient_id'])
    op.create_index('ix_clinical_docs_encounter_id', 'clinical_documentation', ['encounter_id'])
    op.create_index('ix_clinical_docs_type', 'clinical_documentation', ['documentation_type'])

    # ==================== Transcription Records ====================

    op.create_table(
        'transcription_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audio info
        sa.Column('audio_url', sa.String(1000), nullable=True),
        sa.Column('audio_duration_seconds', sa.Float, nullable=True),
        sa.Column('audio_format', sa.String(20), nullable=True),

        # Transcription
        sa.Column('full_text', sa.Text, nullable=False),
        sa.Column('word_count', sa.Integer, default=0),

        # Speaker segments
        sa.Column('segments', postgresql.JSONB, default=[]),
        sa.Column('speaker_count', sa.Integer, default=0),

        # Clinical summary
        sa.Column('clinical_summary', sa.Text, nullable=True),

        # Quality
        sa.Column('confidence_avg', sa.Float, nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),

        # Metadata
        sa.Column('model_version', sa.String(50), default='transcription-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_transcriptions_tenant_id', 'transcription_records', ['tenant_id'])
    op.create_index('ix_transcriptions_patient_id', 'transcription_records', ['patient_id'])
    op.create_index('ix_transcriptions_encounter_id', 'transcription_records', ['encounter_id'])

    # ==================== Entity Extractions ====================

    op.create_table(
        'entity_extractions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Input
        sa.Column('source_text', sa.Text, nullable=False),

        # Entities (array of entity objects)
        sa.Column('entities', postgresql.JSONB, default=[]),
        sa.Column('entity_count', sa.Integer, default=0),

        # Entity counts by type
        sa.Column('condition_count', sa.Integer, default=0),
        sa.Column('medication_count', sa.Integer, default=0),
        sa.Column('procedure_count', sa.Integer, default=0),
        sa.Column('anatomy_count', sa.Integer, default=0),
        sa.Column('lab_count', sa.Integer, default=0),

        # Relationships
        sa.Column('relationships', postgresql.JSONB, default=[]),
        sa.Column('relationship_count', sa.Integer, default=0),

        # Metadata
        sa.Column('model_version', sa.String(50), default='ner-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_entity_extractions_tenant_id', 'entity_extractions', ['tenant_id'])
    op.create_index('ix_entity_extractions_source_doc', 'entity_extractions', ['source_document_id'])

    # ==================== Clinical Decisions ====================

    op.create_table(
        'clinical_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Input
        sa.Column('conditions', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('medications', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('lab_results', postgresql.JSONB, default={}),
        sa.Column('vital_signs', postgresql.JSONB, default={}),
        sa.Column('symptoms', postgresql.ARRAY(sa.String), default=[]),

        # Guidelines
        sa.Column('guideline_recommendations', postgresql.JSONB, default=[]),
        sa.Column('guideline_count', sa.Integer, default=0),

        # Drug interactions
        sa.Column('drug_interactions', postgresql.JSONB, default=[]),
        sa.Column('interaction_count', sa.Integer, default=0),
        sa.Column('has_major_interaction', sa.Boolean, default=False),
        sa.Column('has_contraindication', sa.Boolean, default=False),

        # Differential diagnoses
        sa.Column('differential_diagnoses', postgresql.JSONB, default=[]),

        # Treatment recommendations
        sa.Column('treatment_recommendations', postgresql.JSONB, default=[]),

        # Alerts
        sa.Column('alerts', postgresql.JSONB, default=[]),
        sa.Column('alert_count', sa.Integer, default=0),

        # Provider response
        sa.Column('provider_acknowledged', sa.Boolean, default=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider_action', sa.String(100), nullable=True),
        sa.Column('provider_notes', sa.Text, nullable=True),

        # Metadata
        sa.Column('model_version', sa.String(50), default='cds-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_clinical_decisions_tenant_id', 'clinical_decisions', ['tenant_id'])
    op.create_index('ix_clinical_decisions_patient_id', 'clinical_decisions', ['patient_id'])
    op.create_index('ix_clinical_decisions_encounter_id', 'clinical_decisions', ['encounter_id'])
    op.create_index('ix_clinical_decisions_interactions', 'clinical_decisions', ['has_major_interaction'])

    # ==================== Predictive Analytics ====================

    op.create_table(
        'predictive_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Readmission risk
        sa.Column('readmission_risk_level', sa.Enum('very_low', 'low', 'moderate', 'high',
                                                     'very_high', 'critical',
                                                     name='risk_level'), nullable=True),
        sa.Column('readmission_probability', sa.Float, nullable=True),
        sa.Column('lace_score', sa.Integer, nullable=True),
        sa.Column('lace_components', postgresql.JSONB, default={}),
        sa.Column('readmission_factors', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('readmission_interventions', postgresql.ARRAY(sa.String), default=[]),

        # Deterioration
        sa.Column('deterioration_risk_level', sa.Enum('very_low', 'low', 'moderate', 'high',
                                                       'very_high', 'critical',
                                                       name='risk_level'), nullable=True),
        sa.Column('deterioration_probability', sa.Float, nullable=True),
        sa.Column('mews_score', sa.Integer, nullable=True),
        sa.Column('mews_components', postgresql.JSONB, default={}),
        sa.Column('deterioration_triggers', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('deterioration_actions', postgresql.ARRAY(sa.String), default=[]),

        # No-show prediction
        sa.Column('no_show_risk_level', sa.Enum('very_low', 'low', 'moderate', 'high',
                                                 'very_high', 'critical',
                                                 name='risk_level'), nullable=True),
        sa.Column('no_show_probability', sa.Float, nullable=True),
        sa.Column('no_show_factors', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('no_show_recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Fall risk
        sa.Column('fall_risk_level', sa.Enum('very_low', 'low', 'moderate', 'high',
                                             'very_high', 'critical',
                                             name='risk_level'), nullable=True),
        sa.Column('fall_probability', sa.Float, nullable=True),
        sa.Column('morse_score', sa.Integer, nullable=True),
        sa.Column('morse_components', postgresql.JSONB, default={}),
        sa.Column('fall_risk_factors', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('fall_preventive_measures', postgresql.ARRAY(sa.String), default=[]),

        # Summary
        sa.Column('overall_risk_summary', sa.Text, nullable=True),

        # Metadata
        sa.Column('model_version', sa.String(50), default='pred-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_predictive_tenant_id', 'predictive_analytics', ['tenant_id'])
    op.create_index('ix_predictive_patient_id', 'predictive_analytics', ['patient_id'])
    op.create_index('ix_predictive_readmission_risk', 'predictive_analytics', ['readmission_risk_level'])
    op.create_index('ix_predictive_deterioration_risk', 'predictive_analytics', ['deterioration_risk_level'])
    op.create_index('ix_predictive_created', 'predictive_analytics', ['created_at'])

    # ==================== Image Analyses ====================

    op.create_table(
        'image_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Image info
        sa.Column('image_type', sa.Enum('chest_xray', 'skin_lesion', 'wound', 'ct_scan', 'mri',
                                        name='medical_image_type'), nullable=False),
        sa.Column('image_url', sa.String(1000), nullable=True),
        sa.Column('image_hash', sa.String(64), nullable=True),
        sa.Column('clinical_context', sa.Text, nullable=True),

        # Chest X-ray results
        sa.Column('xray_findings', postgresql.JSONB, default=[]),
        sa.Column('xray_impression', sa.Text, nullable=True),
        sa.Column('xray_critical_findings', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('xray_recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Skin lesion results
        sa.Column('lesion_type', sa.String(100), nullable=True),
        sa.Column('malignancy_risk', sa.String(50), nullable=True),
        sa.Column('abcde_scores', postgresql.JSONB, default={}),
        sa.Column('lesion_differentials', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('urgent_referral', sa.Boolean, default=False),

        # Wound results
        sa.Column('wound_type', sa.String(100), nullable=True),
        sa.Column('wound_stage', sa.String(50), nullable=True),
        sa.Column('tissue_composition', postgresql.JSONB, default={}),
        sa.Column('wound_dimensions', postgresql.JSONB, default={}),
        sa.Column('infection_risk', sa.String(50), nullable=True),
        sa.Column('healing_trajectory', sa.String(100), nullable=True),
        sa.Column('wound_recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Common fields
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Comparison
        sa.Column('comparison_study_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comparison_notes', sa.Text, nullable=True),

        # Metadata
        sa.Column('model_version', sa.String(50), default='image-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_image_analyses_tenant_id', 'image_analyses', ['tenant_id'])
    op.create_index('ix_image_analyses_patient_id', 'image_analyses', ['patient_id'])
    op.create_index('ix_image_analyses_type', 'image_analyses', ['image_type'])
    op.create_index('ix_image_analyses_urgent', 'image_analyses', ['urgent_referral'])

    # ==================== NLP Pipeline Results ====================

    op.create_table(
        'nlp_pipeline_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Input
        sa.Column('source_text', sa.Text, nullable=False),
        sa.Column('document_type', sa.String(100), nullable=True),

        # Sections
        sa.Column('sections', postgresql.JSONB, default=[]),
        sa.Column('section_count', sa.Integer, default=0),

        # Problems
        sa.Column('problems', postgresql.JSONB, default=[]),
        sa.Column('problem_count', sa.Integer, default=0),

        # Medications
        sa.Column('medications', postgresql.JSONB, default=[]),
        sa.Column('medication_count', sa.Integer, default=0),

        # Social determinants
        sa.Column('social_determinants', postgresql.JSONB, default=[]),
        sa.Column('sdoh_count', sa.Integer, default=0),

        # Quality measures
        sa.Column('quality_measures', postgresql.JSONB, default=[]),
        sa.Column('quality_measure_count', sa.Integer, default=0),
        sa.Column('gaps_in_care', postgresql.ARRAY(sa.String), default=[]),

        # Metadata
        sa.Column('model_version', sa.String(50), default='nlp-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_nlp_results_tenant_id', 'nlp_pipeline_results', ['tenant_id'])
    op.create_index('ix_nlp_results_source_doc', 'nlp_pipeline_results', ['source_document_id'])

    # ==================== Voice Biomarker Analyses ====================

    op.create_table(
        'voice_biomarker_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audio info
        sa.Column('audio_url', sa.String(1000), nullable=True),
        sa.Column('audio_duration_seconds', sa.Float, nullable=True),

        # Audio features
        sa.Column('audio_features', postgresql.JSONB, default={}),

        # Depression assessment
        sa.Column('depression_risk', sa.Enum('very_low', 'low', 'moderate', 'high',
                                              'very_high', 'critical',
                                              name='risk_level'), nullable=True),
        sa.Column('phq9_equivalent', sa.Integer, nullable=True),
        sa.Column('depression_confidence', sa.Float, nullable=True),
        sa.Column('depression_markers', postgresql.JSONB, default={}),
        sa.Column('depression_recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Cognitive assessment
        sa.Column('cognitive_risk', sa.Enum('very_low', 'low', 'moderate', 'high',
                                            'very_high', 'critical',
                                            name='risk_level'), nullable=True),
        sa.Column('mci_risk_score', sa.Float, nullable=True),
        sa.Column('fluency_score', sa.Float, nullable=True),
        sa.Column('word_finding_score', sa.Float, nullable=True),
        sa.Column('coherence_score', sa.Float, nullable=True),
        sa.Column('cognitive_concerns', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('cognitive_recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Respiratory assessment
        sa.Column('respiratory_status', sa.String(100), nullable=True),
        sa.Column('breath_support_score', sa.Float, nullable=True),
        sa.Column('detected_patterns', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('respiratory_severity', sa.String(50), nullable=True),
        sa.Column('respiratory_recommendations', postgresql.ARRAY(sa.String), default=[]),

        # Baseline comparison
        sa.Column('baseline_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('baseline_comparison', postgresql.JSONB, default={}),

        # Summary
        sa.Column('overall_summary', sa.Text, nullable=True),

        # Metadata
        sa.Column('model_version', sa.String(50), default='voice-v1.0'),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_voice_analyses_tenant_id', 'voice_biomarker_analyses', ['tenant_id'])
    op.create_index('ix_voice_analyses_patient_id', 'voice_biomarker_analyses', ['patient_id'])
    op.create_index('ix_voice_analyses_depression', 'voice_biomarker_analyses', ['depression_risk'])
    op.create_index('ix_voice_analyses_cognitive', 'voice_biomarker_analyses', ['cognitive_risk'])
    op.create_index('ix_voice_analyses_created', 'voice_biomarker_analyses', ['created_at'])

    # ==================== Medical AI Usage Statistics ====================

    op.create_table(
        'medical_ai_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stats_date', sa.DateTime(timezone=True), nullable=False),

        # Request counts
        sa.Column('triage_requests', sa.Integer, default=0),
        sa.Column('documentation_requests', sa.Integer, default=0),
        sa.Column('entity_extractions', sa.Integer, default=0),
        sa.Column('decision_support_requests', sa.Integer, default=0),
        sa.Column('predictions', sa.Integer, default=0),
        sa.Column('image_analyses', sa.Integer, default=0),
        sa.Column('nlp_pipeline_runs', sa.Integer, default=0),
        sa.Column('voice_analyses', sa.Integer, default=0),

        # Quality metrics
        sa.Column('avg_triage_confidence', sa.Float, default=0),
        sa.Column('avg_processing_time_ms', sa.Float, default=0),
        sa.Column('red_flag_detection_rate', sa.Float, default=0),

        # High-risk alerts
        sa.Column('high_risk_alerts', sa.Integer, default=0),
        sa.Column('critical_findings', sa.Integer, default=0),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_medical_ai_stats_tenant_id', 'medical_ai_stats', ['tenant_id'])
    op.create_index('ix_medical_ai_stats_date', 'medical_ai_stats', ['stats_date'])
    op.create_unique_constraint('uq_medical_ai_stats_tenant_date', 'medical_ai_stats',
                                ['tenant_id', 'stats_date'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('medical_ai_stats')
    op.drop_table('voice_biomarker_analyses')
    op.drop_table('nlp_pipeline_results')
    op.drop_table('image_analyses')
    op.drop_table('predictive_analytics')
    op.drop_table('clinical_decisions')
    op.drop_table('entity_extractions')
    op.drop_table('transcription_records')
    op.drop_table('clinical_documentation')
    op.drop_table('medical_triage_results')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS medical_image_type')
    op.execute('DROP TYPE IF EXISTS documentation_type')
    op.execute('DROP TYPE IF EXISTS interaction_severity')
    op.execute('DROP TYPE IF EXISTS negation_status')
    op.execute('DROP TYPE IF EXISTS medical_entity_type')
    op.execute('DROP TYPE IF EXISTS risk_level')
    op.execute('DROP TYPE IF EXISTS urgency_level')
