-- =============================================================================
-- PostgreSQL Initialization Script for PRM Service
-- Runs automatically when the container is first created
-- =============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";    -- For GIN indexes

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS prm;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS fhir;

-- Grant permissions
GRANT ALL ON SCHEMA prm TO CURRENT_USER;
GRANT ALL ON SCHEMA audit TO CURRENT_USER;
GRANT ALL ON SCHEMA fhir TO CURRENT_USER;

-- Set default search path
ALTER DATABASE CURRENT_DATABASE SET search_path TO public, prm, fhir;

-- Create audit log table for HIPAA compliance
CREATE TABLE IF NOT EXISTS audit.access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    request_path TEXT,
    request_method VARCHAR(10),
    response_status INTEGER,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.access_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit.access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit.access_log(resource_type, resource_id);

-- Create voice call logs table for Zoice integration
CREATE TABLE IF NOT EXISTS prm.voice_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id VARCHAR(255) UNIQUE NOT NULL,
    patient_id UUID,
    practitioner_id UUID,
    call_type VARCHAR(50),  -- inbound, outbound
    status VARCHAR(50),     -- initiated, ringing, answered, completed, failed
    duration_seconds INTEGER,
    recording_url TEXT,
    transcript TEXT,
    transcript_summary TEXT,
    sentiment_score FLOAT,
    call_metadata JSONB,
    zoice_pipeline_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_call_patient ON prm.voice_call_logs(patient_id);
CREATE INDEX IF NOT EXISTS idx_voice_call_status ON prm.voice_call_logs(status);
CREATE INDEX IF NOT EXISTS idx_voice_call_created ON prm.voice_call_logs(created_at);

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'PRM Database initialized successfully at %', NOW();
END $$;
