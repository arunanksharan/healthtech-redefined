-- ============================================================================
-- FHIR R4 Tables Migration
-- Created: 2024-11-24
-- Description: Add tables for FHIR R4 resource storage
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- FHIR Resource Storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS fhir_resources (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Tenant for multi-tenancy
    tenant_id UUID NOT NULL,
    
    -- Resource type (Patient, Practitioner, Observation, etc.)
    resource_type VARCHAR(50) NOT NULL,
    
    -- FHIR resource ID (unique within resource_type and tenant)
    fhir_id VARCHAR(64) NOT NULL,
    
    -- Version control
    version_id INTEGER NOT NULL DEFAULT 1,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- JSONB storage for the complete FHIR resource
    resource_data JSONB NOT NULL,
    
    -- Search optimization - extracted tokens for common search parameters
    search_tokens JSONB DEFAULT '{}'::jsonb,
    
    -- Full-text search - extracted searchable strings
    search_strings TSVECTOR,
    
    -- Metadata
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique constraint on tenant, resource_type, fhir_id (for current, non-deleted resources)
CREATE UNIQUE INDEX idx_fhir_resources_unique 
ON fhir_resources (tenant_id, resource_type, fhir_id) 
WHERE (deleted = FALSE);

-- Search indexes
CREATE INDEX idx_fhir_resources_tenant_type ON fhir_resources (tenant_id, resource_type);
CREATE INDEX idx_fhir_resources_fhir_id ON fhir_resources (fhir_id);
CREATE INDEX idx_fhir_resources_type ON fhir_resources (resource_type);
CREATE INDEX idx_fhir_resources_deleted ON fhir_resources (deleted);
CREATE INDEX idx_fhir_resources_last_updated ON fhir_resources (last_updated);

-- GIN indexes for JSONB search optimization
CREATE INDEX idx_fhir_resources_data ON fhir_resources USING GIN (resource_data);
CREATE INDEX idx_fhir_resources_search_tokens ON fhir_resources USING GIN (search_tokens);

-- Full-text search index
CREATE INDEX idx_fhir_resources_search_strings ON fhir_resources USING GIN (search_strings);

-- Comments
COMMENT ON TABLE fhir_resources IS 'Generic FHIR resource storage with JSONB';
COMMENT ON COLUMN fhir_resources.resource_data IS 'Complete FHIR resource as JSON';
COMMENT ON COLUMN fhir_resources.search_tokens IS 'Extracted search tokens for optimization';
COMMENT ON COLUMN fhir_resources.search_strings IS 'Full-text search vectors';

-- ============================================================================
-- FHIR Resource History
-- ============================================================================

CREATE TABLE IF NOT EXISTS fhir_resource_history (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Reference to the current resource
    resource_id UUID NOT NULL,
    
    -- Tenant
    tenant_id UUID NOT NULL,
    
    -- Resource identification
    resource_type VARCHAR(50) NOT NULL,
    fhir_id VARCHAR(64) NOT NULL,
    
    -- Version information
    version_id INTEGER NOT NULL,
    
    -- Snapshot of the resource at this version
    resource_data JSONB NOT NULL,
    
    -- Operation that created this version
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('create', 'update', 'delete')),
    
    -- Change metadata
    changed_by VARCHAR(255),
    change_reason TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for history
CREATE INDEX idx_fhir_history_resource ON fhir_resource_history (resource_id);
CREATE INDEX idx_fhir_history_tenant_type_id ON fhir_resource_history (tenant_id, resource_type, fhir_id);
CREATE INDEX idx_fhir_history_version ON fhir_resource_history (resource_id, version_id);
CREATE INDEX idx_fhir_history_changed_at ON fhir_resource_history (changed_at);

-- Comments
COMMENT ON TABLE fhir_resource_history IS 'Version history for FHIR resources';
COMMENT ON COLUMN fhir_resource_history.operation IS 'create, update, or delete';

-- ============================================================================
-- FHIR Code Systems
-- ============================================================================

CREATE TABLE IF NOT EXISTS fhir_code_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    
    -- CodeSystem identification
    url VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'active', 'retired')),
    
    -- Content
    content VARCHAR(20) NOT NULL CHECK (content IN ('not-present', 'example', 'fragment', 'complete')),
    count INTEGER,
    
    -- Full CodeSystem resource
    resource_data JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fhir_codesystems_tenant ON fhir_code_systems (tenant_id);
CREATE INDEX idx_fhir_codesystems_url ON fhir_code_systems (url);
CREATE INDEX idx_fhir_codesystems_status ON fhir_code_systems (status);

-- Comments
COMMENT ON TABLE fhir_code_systems IS 'FHIR CodeSystem resources for terminology';

-- ============================================================================
-- FHIR Value Sets
-- ============================================================================

CREATE TABLE IF NOT EXISTS fhir_value_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    
    -- ValueSet identification
    url VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'active', 'retired')),
    
    -- Expansion (pre-computed if available)
    expansion_data JSONB,
    expansion_timestamp TIMESTAMPTZ,
    
    -- Full ValueSet resource
    resource_data JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fhir_valuesets_tenant ON fhir_value_sets (tenant_id);
CREATE INDEX idx_fhir_valuesets_url ON fhir_value_sets (url);
CREATE INDEX idx_fhir_valuesets_status ON fhir_value_sets (status);

-- Comments
COMMENT ON TABLE fhir_value_sets IS 'FHIR ValueSet resources for coded values';

-- ============================================================================
-- FHIR Concept Maps
-- ============================================================================

CREATE TABLE IF NOT EXISTS fhir_concept_maps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    
    -- ConceptMap identification
    url VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'active', 'retired')),
    
    -- Source and target
    source_url VARCHAR(255),
    target_url VARCHAR(255),
    
    -- Full ConceptMap resource
    resource_data JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fhir_conceptmaps_tenant ON fhir_concept_maps (tenant_id);
CREATE INDEX idx_fhir_conceptmaps_url ON fhir_concept_maps (url);
CREATE INDEX idx_fhir_conceptmaps_source_target ON fhir_concept_maps (source_url, target_url);

-- Comments
COMMENT ON TABLE fhir_concept_maps IS 'FHIR ConceptMap resources for code mappings';

-- ============================================================================
-- FHIR Subscriptions
-- ============================================================================

CREATE TABLE IF NOT EXISTS fhir_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    
    -- Subscription details
    fhir_id VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('requested', 'active', 'error', 'off')),
    
    -- Criteria
    criteria TEXT NOT NULL,
    resource_type VARCHAR(50),
    
    -- Channel
    channel_type VARCHAR(20) NOT NULL CHECK (channel_type IN ('rest-hook', 'websocket', 'email')),
    channel_endpoint VARCHAR(500),
    channel_payload VARCHAR(20) NOT NULL DEFAULT 'application/fhir+json',
    channel_headers JSONB,
    
    -- Error tracking
    error_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,
    
    -- Delivery tracking
    last_triggered_at TIMESTAMPTZ,
    delivery_count INTEGER NOT NULL DEFAULT 0,
    
    -- Full Subscription resource
    resource_data JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fhir_subscriptions_tenant ON fhir_subscriptions (tenant_id);
CREATE INDEX idx_fhir_subscriptions_status ON fhir_subscriptions (status);
CREATE INDEX idx_fhir_subscriptions_resource_type ON fhir_subscriptions (resource_type);
CREATE INDEX idx_fhir_subscriptions_active ON fhir_subscriptions (tenant_id, status) WHERE (status = 'active');

-- Comments
COMMENT ON TABLE fhir_subscriptions IS 'FHIR Subscription resources for notifications';

-- ============================================================================
-- Trigger for updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_fhir_code_systems_updated_at BEFORE UPDATE ON fhir_code_systems
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fhir_value_sets_updated_at BEFORE UPDATE ON fhir_value_sets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fhir_concept_maps_updated_at BEFORE UPDATE ON fhir_concept_maps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fhir_subscriptions_updated_at BEFORE UPDATE ON fhir_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Insert migration record
-- This would be handled by Alembic in practice
-- INSERT INTO alembic_version (version_num) VALUES ('fhir_r4_tables_001');
