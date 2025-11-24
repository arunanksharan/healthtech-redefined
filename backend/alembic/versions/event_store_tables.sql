-- Event Store Tables Migration
-- Creates tables for event sourcing, snapshots, and dead letter queue

-- ============================================================================
-- STORED EVENTS TABLE (Event Store)
-- ============================================================================

CREATE TABLE IF NOT EXISTS stored_events (
    event_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    version INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Ensure version uniqueness per aggregate
    CONSTRAINT unique_aggregate_version UNIQUE (aggregate_id, version),

    -- Foreign key to tenants (if exists)
    CONSTRAINT fk_stored_events_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenants(id)
        ON DELETE CASCADE
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_stored_events_aggregate
    ON stored_events(aggregate_id, version);

CREATE INDEX IF NOT EXISTS idx_stored_events_type_time
    ON stored_events(event_type, occurred_at);

CREATE INDEX IF NOT EXISTS idx_stored_events_tenant_time
    ON stored_events(tenant_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_stored_events_aggregate_type
    ON stored_events(aggregate_type, occurred_at);

-- Comment
COMMENT ON TABLE stored_events IS
    'Event store for event sourcing pattern. Stores domain events for aggregate reconstruction and replay.';

-- ============================================================================
-- AGGREGATE SNAPSHOTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS aggregate_snapshots (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    version INTEGER NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Foreign key to tenants (if exists)
    CONSTRAINT fk_aggregate_snapshots_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenants(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_aggregate_snapshots_aggregate
    ON aggregate_snapshots(aggregate_id, version DESC);

CREATE INDEX IF NOT EXISTS idx_aggregate_snapshots_type
    ON aggregate_snapshots(aggregate_type, created_at);

-- Comment
COMMENT ON TABLE aggregate_snapshots IS
    'Snapshots of aggregate state for performance. Allows rebuilding aggregates without replaying all events.';

-- ============================================================================
-- FAILED EVENTS TABLE (Dead Letter Queue)
-- ============================================================================

CREATE TABLE IF NOT EXISTS failed_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_payload JSONB NOT NULL,
    error_type VARCHAR(255) NOT NULL,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    failed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    retried BOOLEAN NOT NULL DEFAULT FALSE,
    retried_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Foreign key to tenants (if exists)
    CONSTRAINT fk_failed_events_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenants(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_failed_events_event_id
    ON failed_events(event_id);

CREATE INDEX IF NOT EXISTS idx_failed_events_type_time
    ON failed_events(event_type, failed_at);

CREATE INDEX IF NOT EXISTS idx_failed_events_status
    ON failed_events(resolved, failed_at);

CREATE INDEX IF NOT EXISTS idx_failed_events_tenant
    ON failed_events(tenant_id, failed_at);

-- Comment
COMMENT ON TABLE failed_events IS
    'Dead Letter Queue for events that failed to process. Stores failed events for debugging and retry.';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get latest snapshot for aggregate
CREATE OR REPLACE FUNCTION get_latest_snapshot(p_aggregate_id UUID)
RETURNS TABLE (
    id UUID,
    aggregate_type VARCHAR(100),
    version INTEGER,
    state JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.aggregate_type,
        s.version,
        s.state,
        s.created_at
    FROM aggregate_snapshots s
    WHERE s.aggregate_id = p_aggregate_id
    ORDER BY s.version DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get event count for aggregate
CREATE OR REPLACE FUNCTION get_aggregate_event_count(p_aggregate_id UUID)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM stored_events
        WHERE aggregate_id = p_aggregate_id
    );
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old snapshots (keep latest 5)
CREATE OR REPLACE FUNCTION cleanup_old_snapshots(p_aggregate_id UUID)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH snapshots_to_delete AS (
        SELECT id
        FROM aggregate_snapshots
        WHERE aggregate_id = p_aggregate_id
        ORDER BY version DESC
        OFFSET 5
    )
    DELETE FROM aggregate_snapshots
    WHERE id IN (SELECT id FROM snapshots_to_delete);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for event stream by tenant
CREATE OR REPLACE VIEW v_tenant_event_stream AS
SELECT
    e.event_id,
    e.tenant_id,
    e.event_type,
    e.aggregate_type,
    e.aggregate_id,
    e.version,
    e.event_data,
    e.occurred_at,
    e.metadata
FROM stored_events e
ORDER BY e.occurred_at DESC;

-- View for unresolved DLQ events
CREATE OR REPLACE VIEW v_unresolved_dlq_events AS
SELECT
    f.id,
    f.tenant_id,
    f.event_id,
    f.event_type,
    f.error_type,
    f.error_message,
    f.retry_count,
    f.failed_at,
    EXTRACT(EPOCH FROM (NOW() - f.failed_at)) / 3600 AS hours_since_failure
FROM failed_events f
WHERE f.resolved = FALSE
ORDER BY f.failed_at DESC;

-- ============================================================================
-- STATISTICS
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE stored_events;
ANALYZE aggregate_snapshots;
ANALYZE failed_events;

-- ============================================================================
-- GRANTS (adjust as needed)
-- ============================================================================

-- Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE ON stored_events TO healthtech_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON aggregate_snapshots TO healthtech_app;
-- GRANT SELECT, INSERT, UPDATE ON failed_events TO healthtech_app;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables were created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN ('stored_events', 'aggregate_snapshots', 'failed_events')
    AND table_schema = 'public';

    IF table_count = 3 THEN
        RAISE NOTICE 'SUCCESS: All event store tables created successfully';
    ELSE
        RAISE EXCEPTION 'ERROR: Some tables were not created. Expected 3, found %', table_count;
    END IF;
END $$;

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Uncomment to insert sample data
/*
INSERT INTO stored_events (
    event_id,
    tenant_id,
    aggregate_type,
    aggregate_id,
    version,
    event_type,
    event_data,
    occurred_at
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM tenants LIMIT 1),
    'Patient',
    gen_random_uuid(),
    1,
    'Patient.Created',
    '{"patient_id": "PAT-123", "name": "John Doe", "email": "john@example.com"}'::jsonb,
    NOW()
);
*/
