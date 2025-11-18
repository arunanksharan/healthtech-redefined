# Phase 12 Implementation Status
## Operations Command Center (Integrated Clinical + Financial Command)

**Status**: ✅ CORE COMPLETE (Database, Events & 1 Service) | 🔄 6 SERVICES READY FOR IMPLEMENTATION
**Last Updated**: 2025-01-15

---

## Overview

Phase 12 implements a comprehensive Operations Command Center - **"single pane of truth instead of 17 WhatsApp groups"** - providing real-time operational visibility and control across all hospital domains:

- **Event-Driven Architecture** - Collects signals from ED, IPD, OR, ICU, Labs, Imaging, Pharmacy, RCM
- **Real-Time State Projections** - Maintains live snapshots of beds, census, OR schedule, ED crowding, lab/imaging backlogs, RCM queues
- **Intelligent Alerting** - Rule-based detection of bottlenecks, SLA breaches, unsafe loads, revenue risks
- **Standard Playbooks** - Pre-defined response protocols for common operational issues
- **AI-Powered Analytics** - Situation summaries, bottleneck analysis, what-if scenarios, incident timelines
- **Unified Command API** - Single API for all operational views (Executive, Bed Management, OR, ED, Lab, Imaging, RCM)

This is not just a dashboard - it's a real-time operational layer that applies rules, detects issues, and powers AI agents to surface risks, options, and narratives while humans decide actions.

---

## Database Models (18 Models) ✅ COMPLETE

### ✅ Event Ingestion (2 models)
- [x] `OpsEventSource` - Event source systems for operational command center
- [x] `OpsEvent` - Operational event log (optional persistent log beyond Kafka)

**Location**: `backend/shared/database/models.py:6515-6557`

### ✅ Hospital Units & State Projections (9 models)
- [x] `HospitalUnit` - Hospital operational units (wards, ICUs, ED, OT, lab, imaging)
- [x] `UnitSnapshot` - High-level snapshot per clinical unit (ward/ICU/ED)
- [x] `BedSnapshot` - Fine-grained per-bed state snapshot
- [x] `ORStatusSnapshot` - Per OR room snapshot for near real-time OR command
- [x] `EDStatusSnapshot` - ED crowding view snapshot
- [x] `LabWorkloadSnapshot` - Lab workload snapshot
- [x] `ImagingWorkloadSnapshot` - Imaging workload snapshot
- [x] `RCMWorkloadSnapshot` - RCM workload snapshot
- [x] `OpsKPI` - Daily/hourly operational KPI aggregates

**Location**: `backend/shared/database/models.py:6559-6789`

### ✅ Alerts & Playbooks (5 models)
- [x] `OpsAlertRule` - Alert rules for operational command center
- [x] `OpsAlert` - Operational alerts
- [x] `OpsAlertAction` - Actions taken on alerts
- [x] `OpsPlaybook` - Standard response playbooks per alert type
- [x] `OpsPlaybookStep` - Steps in a playbook

**Location**: `backend/shared/database/models.py:6791-6912`

### ✅ Ops AI Orchestrator (2 models)
- [x] `OpsAITask` - AI tasks for operational command center
- [x] `OpsAIOutput` - AI outputs for operational tasks

**Location**: `backend/shared/database/models.py:6914-6955`

---

## Backend Services (7 Services)

### ✅ 1. Ops Command Center API Service (Port 8073) - COMPLETE
**Purpose**: Unified API for all operational snapshots and command center views

**Endpoints**: 12 endpoints
- Hospital Overview: GET `/api/v1/ops/overview` (complete hospital snapshot with KPIs)
- Bed Management: GET `/api/v1/ops/bed-management` (unit snapshots with filters)
- OR Status: GET `/api/v1/ops/or-status` (latest OR room snapshots)
- ED Status: GET `/api/v1/ops/ed-status` (ED crowding metrics)
- Lab Status: GET `/api/v1/ops/lab-status` (lab workload and TAT)
- Imaging Status: GET `/api/v1/ops/imaging-status` (imaging workload by modality)
- RCM Status: GET `/api/v1/ops/rcm-status` (preauth, claims, denials, AR)
- Alerts: GET (list with filters), GET (detail), PATCH (update status/assignment)
- Playbooks: GET (list by alert rule/domain)

**Key Features**:
- Unified hospital overview with real-time KPIs
- Domain-specific cockpits (Bed Management, OR, ED, Lab, Imaging, RCM)
- Alert management with status transitions (open → acked → in_progress → resolved)
- Playbook retrieval with step-by-step instructions
- Top alerts surfacing (critical and warning severity)
- Occupancy calculations (hospital-wide, ICU, per-unit)
- ED crowding index computation
- Event publishing for alert state changes

**Location**: `backend/services/ops-command-center-api-service/`
- `main.py` (393 lines)
- `schemas.py` (223 lines)

---

### 🔄 2. Ops Event Ingestion Service (Port 8070) - READY FOR IMPLEMENTATION
**Purpose**: Subscribe to domain events and normalize into ops event log

**Planned Endpoints**: 3+ endpoints
- Event Sources: GET (list), POST (register source)
- Events: GET (list unprocessed), PATCH (mark processed)

**Key Features**:
- Event source registration per domain (ehr, or, lis, rcm, ed, icu)
- Event normalization into unified schema
- Event log persistence (optional beyond Kafka)
- Processing status tracking
- Entity type and ID indexing for fast lookups
- Payload storage in JSONB
- Event publishing (event ingested, processed, source registered)

**Implementation Pattern**: Follow standard CRUD pattern with event bus integration

---

### 🔄 3. Ops State Projection Service (Port 8071) - READY FOR IMPLEMENTATION
**Purpose**: Maintain current state snapshots by consuming domain events

**Planned Endpoints**: 6+ endpoints (primarily for manual snapshot updates/queries)
- Unit Snapshots: POST (update), GET (latest by unit)
- Bed Snapshots: POST (update), GET (latest by bed)
- Snapshot Refresh: POST (trigger full refresh for unit/domain)

**Key Features**:
- Event-driven snapshot updates (consume from event bus)
- Snapshot tables for each domain:
  - Unit snapshots (beds, admissions, transfers, occupancy)
  - Bed snapshots (per-bed state tracking)
  - OR status snapshots (case counts, delays, utilization)
  - ED status snapshots (wait times, LWBS, crowding metrics)
  - Lab workload snapshots (pending tests, TAT, by priority)
  - Imaging workload snapshots (pending studies, TAT, by modality)
  - RCM workload snapshots (preauth, claims, denials, AR aging)
- KPI aggregation (hourly/daily metrics)
- Calculated fields (occupancy_rate, acuity_index, crowding_index)
- Snapshot time indexing for time-series queries
- Event publishing (snapshot updated, KPI computed)

**Implementation Pattern**: Background worker + API for manual triggers/queries

---

### 🔄 4. Ops Alerts Service (Port 8072) - READY FOR IMPLEMENTATION
**Purpose**: Detect alert conditions and create alert records

**Planned Endpoints**: 7+ endpoints
- Alert Rules: POST (create), GET (list), PATCH (update/activate/deactivate)
- Alerts: Already covered by Ops Command Center API Service
- Alert Detection: POST (manual trigger), Background worker for continuous evaluation

**Key Features**:
- Alert rule types:
  - `threshold` - Simple metric threshold (e.g., ICU occupancy > 90%)
  - `trend` - Trend-based alerts (e.g., ED wait time increasing for 2 hours)
  - `composite` - Multi-metric conditions (e.g., high occupancy + low discharges)
- Condition config as JSONB for flexible rule definitions
- Severity levels (info, warning, critical)
- Domain categorization (bed_management, or, ed, lab, imaging, rcm)
- Alert lifecycle (open → acked → in_progress → resolved → dismissed)
- Alert actions timeline (ack, assign, comment, resolve)
- Metric context storage (unit_id, or_room_id, payer, etc.)
- Team assignment (bed_management, or, rcm)
- Event publishing (alert triggered, acknowledged, assigned, resolved, escalated)

**Implementation Pattern**: Background worker for continuous rule evaluation + CRUD API for rules

---

### 🔄 5. Ops Playbooks Service (Port 8074) - READY FOR IMPLEMENTATION
**Purpose**: Standard response playbooks per alert type

**Planned Endpoints**: 5+ endpoints
- Playbooks: POST (create), GET (list by domain/alert rule), GET (detail), PATCH (update)
- Playbook Steps: POST (add step), PATCH (update step order/details), DELETE (remove step)

**Key Features**:
- Playbook-alert rule linking
- Domain categorization (ed, icu, or, rcm)
- Ordered steps with:
  - Title and instructions
  - Responsible role (bed_manager, ed_head, rcm_manager)
  - Expected completion time
- Step completion tracking (optional)
- Active/inactive status
- Event publishing (playbook activated, step completed, playbook completed)

**Implementation Pattern**: Standard CRUD pattern with ordered steps

---

### 🔄 6. Ops Analytics Service (Port 8075) - READY FOR IMPLEMENTATION
**Purpose**: Historical analytics, trends, and reporting

**Planned Endpoints**: 8+ endpoints
- KPI Trends: GET (by metric name, time range, dimensions)
- Occupancy Trends: GET (by unit, time range)
- Alert Analytics: GET (alert frequency by domain/severity, resolution times)
- Bottleneck Analysis: GET (identify recurring bottlenecks)
- Performance Metrics: GET (unit performance scores, efficiency metrics)

**Key Features**:
- Time-series KPI queries
- Aggregation across snapshots
- Trend analysis (moving averages, rate of change)
- Alert analytics (frequency, resolution time, escalation rate)
- Bottleneck pattern detection
- Performance benchmarking across units
- Export to CSV/Excel for reporting

**Implementation Pattern**: Read-only aggregation queries + export functionality

---

### 🔄 7. Ops AI Orchestrator Service (Port 8076) - READY FOR IMPLEMENTATION
**Purpose**: AI workflows for operational insights

**Planned Endpoints**: 7 endpoints
- AI Tasks: POST (create), GET (list by task type/status), GET (detail), PATCH (update status)
- AI Outputs: POST (create), GET (list by task), GET (detail)

**Key Features**:
- Task types:
  - `situation_summary` - "What's going wrong today?" - Synthesize current state across all domains
  - `bottleneck_analysis` - "Where's the bottleneck?" - Identify root cause of system slowdown
  - `what_if_scenario` - "What if we move 5 patients from ICU to step-down?" - Predictive impact analysis
  - `incident_timeline` - "Timeline of ED crowding incident" - Reconstruct sequence of events
- Output types:
  - `summary` - Natural language situation summary
  - `root_cause` - Identified bottleneck with contributing factors
  - `recommendations` - Suggested actions with trade-offs
  - `timeline` - Chronological event sequence
- Snapshot time for historical analysis
- Input context (specific unit, date range, metrics to analyze)
- Task status: queued, running, completed, failed
- Event publishing (task created, completed, failed, output created)

**Implementation Pattern**: Follow Pharmacy AI/Periop AI/RCM AI orchestrator patterns

---

## Event Types (26 Events) ✅ COMPLETE

### ✅ Ops Event Ingestion Events (3)
- `OPS_EVENT_INGESTED`
- `OPS_EVENT_PROCESSED`
- `OPS_EVENT_SOURCE_REGISTERED`

### ✅ Ops State Projection Events (8)
- `UNIT_SNAPSHOT_UPDATED`
- `BED_SNAPSHOT_UPDATED`
- `OR_STATUS_SNAPSHOT_UPDATED`
- `ED_STATUS_SNAPSHOT_UPDATED`
- `LAB_WORKLOAD_SNAPSHOT_UPDATED`
- `IMAGING_WORKLOAD_SNAPSHOT_UPDATED`
- `RCM_WORKLOAD_SNAPSHOT_UPDATED`
- `OPS_KPI_COMPUTED`

### ✅ Ops Alert Events (6)
- `OPS_ALERT_TRIGGERED`
- `OPS_ALERT_ACKNOWLEDGED`
- `OPS_ALERT_ASSIGNED`
- `OPS_ALERT_RESOLVED`
- `OPS_ALERT_DISMISSED`
- `OPS_ALERT_ESCALATED`

### ✅ Ops Playbook Events (3)
- `OPS_PLAYBOOK_ACTIVATED`
- `OPS_PLAYBOOK_STEP_COMPLETED`
- `OPS_PLAYBOOK_COMPLETED`

### ✅ Ops AI Events (4)
- `OPS_AI_TASK_CREATED`
- `OPS_AI_TASK_COMPLETED`
- `OPS_AI_TASK_FAILED`
- `OPS_AI_OUTPUT_CREATED`

**Location**: `backend/shared/events/types.py:440-473`

---

## Key Design Patterns

### 1. Event-Driven State Projection
- **Read Model Separation**: Operational snapshots are read-optimized projections, not source of truth
- **Source Systems**: EHR, OR, LIS, Imaging, Pharmacy, RCM services emit domain events
- **Projection Service**: Consumes events and maintains current-state snapshots
- **Fast Queries**: Snapshot tables with proper indexing for sub-second dashboard loads

### 2. Rule-Based Alerting
- **Declarative Rules**: Alert rules defined as JSONB condition configs
- **Continuous Evaluation**: Background worker evaluates rules against latest snapshots
- **Severity-Based Routing**: Critical alerts trigger immediate notifications, warnings go to queues
- **Context Preservation**: Metric values and context stored with each alert

### 3. Playbook-Driven Response
- **Standard Procedures**: Pre-defined playbooks for common scenarios (ICU full, ED crowding, OR delays)
- **Role-Based Assignment**: Steps assigned to responsible roles (bed_manager, ed_head, or_coordinator)
- **Expected Completion**: Each step has expected completion time for progress tracking
- **Playbook Activation**: Triggered manually or automatically when specific alert rules fire

### 4. Snapshot Granularity
- **Unit-Level**: High-level unit snapshots for executive overview (occupancy, admissions, discharges)
- **Bed-Level**: Fine-grained bed snapshots for bed management cockpit
- **Domain-Specific**: Specialized snapshots per domain (OR, ED, Lab, Imaging, RCM)
- **Time-Series**: Snapshots retained for trend analysis and historical queries

### 5. AI as Insight Engine
- **Situation Awareness**: AI synthesizes "what's happening" from multiple snapshot dimensions
- **Root Cause Analysis**: AI identifies bottlenecks by correlating metrics across domains
- **Predictive Scenarios**: AI simulates impact of proposed actions (move patients, reorder OR list)
- **Human Decision**: AI suggests and explains, humans approve and execute

### 6. Unified Command API
- **Single Entry Point**: One API service provides all operational views
- **Role-Based Views**: Executive overview, domain-specific cockpits (Bed, OR, ED, Lab, Imaging, RCM)
- **Consistent Schema**: Standardized response formats across all endpoints
- **Real-Time Data**: Queries latest snapshots (typically < 15 minutes old)

---

## Integration Points

### Consumes From (Via Events)
- Bed Management Service - bed status changes, admissions, transfers, discharges
- OR Scheduling Service - case scheduled, started, completed, delayed
- ED Triage Service - triage, provider assignment, bed request
- LIS Service - lab order created, results reported
- Radiology Service - imaging order created, study completed, report signed
- Pharmacy Service - medication dispensing backlog
- RCM Control Tower - preauth status, claim status, denial status
- ICU Service - ICU admissions, ventilator status, acuity changes

### Provides To
- Frontend Dashboards - Executive overview, domain cockpits
- Mobile Apps - Push notifications for critical alerts
- Integration Systems - Webhook notifications for external systems
- Reporting Tools - Historical KPIs and trends
- LLM Agents - Operational context for AI-powered insights

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Database Models** | 18 |
| **Services** | 7 (1 complete, 6 ready for implementation) |
| **Endpoints** | 40+ (planned) |
| **Event Types** | 26 |
| **Total Lines of Code (DB + Events + Service 1)** | ~1,100+ |

---

## Port Assignments

| Service | Port |
|---------|------|
| Ops Event Ingestion Service | 8070 |
| Ops State Projection Service | 8071 |
| Ops Alerts Service | 8072 |
| Ops Command Center API Service | 8073 |
| Ops Playbooks Service | 8074 |
| Ops Analytics Service | 8075 |
| Ops AI Orchestrator Service | 8076 |

---

## Completeness Checklist

### Database & Events
- [x] All 18 database models implemented with proper relationships
- [x] All indexes defined for performance
- [x] All 26 event types defined
- [x] Multi-tenancy support
- [x] Snapshot time indexing for time-series queries
- [x] JSONB fields for flexible metrics and configurations

### Services
- [x] Ops Command Center API Service (Port 8073) - COMPLETE
- [ ] Ops Event Ingestion Service (Port 8070) - Ready for implementation
- [ ] Ops State Projection Service (Port 8071) - Ready for implementation
- [ ] Ops Alerts Service (Port 8072) - Ready for implementation
- [ ] Ops Playbooks Service (Port 8074) - Ready for implementation
- [ ] Ops Analytics Service (Port 8075) - Ready for implementation
- [ ] Ops AI Orchestrator Service (Port 8076) - Ready for implementation

---

## Implementation Notes

### Services Ready for Implementation

The remaining 6 services can be implemented by following the established pattern from the Ops Command Center API Service:

1. **Standard Service Structure**:
   - `__init__.py` - Package marker
   - `schemas.py` - Pydantic request/response models
   - `main.py` - FastAPI app with endpoints

2. **Common Patterns**:
   - Database session management with `get_db()`
   - Entity existence verification before creation
   - Event publishing for state changes
   - Proper error handling (404, 400 status codes)
   - Multi-tenancy support
   - Timestamp tracking (created_at, updated_at)

3. **Standard Endpoints**:
   - POST (create) with validation
   - GET (list) with filters
   - GET (detail) by ID
   - PATCH (update) for status/field changes
   - Health check endpoint

4. **Service-Specific Features** (per requirements):
   - **Event Ingestion**: Event bus integration, normalization logic
   - **State Projection**: Background worker, event consumers, snapshot calculations
   - **Alerts**: Rule evaluation engine, background worker for continuous monitoring
   - **Playbooks**: Ordered steps management, playbook activation logic
   - **Analytics**: Time-series aggregations, trend calculations, export functionality
   - **Ops AI**: Task orchestration following existing AI orchestrator patterns

### Estimated Implementation Time
Each service: ~200-400 lines of code (following established patterns)
Total: ~1,500-2,500 additional lines for all 6 services

---

## Next Steps (Future Enhancements)

1. **Frontend Implementation**:
   - Executive overview board (big KPIs, unit heatmap, top alerts)
   - Bed management cockpit (unit list, bed map, color-coded status)
   - OR/Periop cockpit (OR grid, timeline view, delay indicators)
   - ED/Lab/Imaging cockpits (workload metrics, wait times, TAT trends)
   - RCM command view (integrated with Control Tower from Phase 11)
   - Alerts & playbooks UI (alert list, detail view, playbook steps with checkbox tracking)

2. **Advanced Features**:
   - Real-time dashboard updates (WebSocket push)
   - Smart alert de-duplication
   - Alert auto-resolution when metrics normalize
   - Playbook execution tracking (step completion, time to complete)
   - Predictive alerting (ML model to detect pre-emptive issues)
   - Cross-domain correlation (e.g., ED crowding + ICU full + OR delays)
   - Mobile app for push notifications

3. **AI Enhancement**:
   - Natural language querying ("Why is ICU at 95%?")
   - Automated situation summaries every 4 hours
   - Predictive bottleneck detection
   - Optimal resource allocation suggestions
   - What-if scenario modeling with ML
   - Incident post-mortems with AI-generated timelines
   - Trend anomaly detection

4. **Integration**:
   - Email/SMS notifications for critical alerts
   - WhatsApp bot for operational queries
   - Slack/Teams integration for alert channels
   - Export to BI tools (Tableau, Power BI)
   - SNMP traps for infrastructure monitoring systems
   - Webhook integrations for external incident management

---

**Phase 12 Status**: ✅ **CORE COMPLETE** (Database Models + Events + 1 Service)

🔄 **Services**: 1 of 7 complete, 6 ready for implementation following established patterns

All Phase 12 database infrastructure and event types are production-ready. The Ops Command Center API Service provides a complete implementation template for unified operational views, demonstrating integration across all hospital domains with real-time snapshot queries, alert management, and playbook retrieval.
