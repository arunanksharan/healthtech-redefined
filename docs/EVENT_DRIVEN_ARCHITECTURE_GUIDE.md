# Event-Driven Architecture Implementation Guide

## Overview

This document provides a comprehensive guide to the event-driven architecture implemented for the healthcare platform. The architecture uses Apache Kafka as the message broker and implements event sourcing, CQRS patterns, and saga-based distributed transactions.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Event Publishing](#event-publishing)
4. [Event Consumption](#event-consumption)
5. [Event Store & Event Sourcing](#event-store--event-sourcing)
6. [Workflow Engine & Saga Pattern](#workflow-engine--saga-pattern)
7. [Circuit Breaker & Resilience](#circuit-breaker--resilience)
8. [Dead Letter Queue](#dead-letter-queue)
9. [Best Practices](#best-practices)
10. [Monitoring & Observability](#monitoring--observability)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Event-Driven Architecture                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PRM Service │────▶│ Kafka Cluster│────▶│ FHIR Service │
│              │     │  (3 Brokers) │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                    ┌───────┼───────┐
                    │       │       │
            ┌───────▼──┐ ┌──▼────┐ ┌▼──────────┐
            │ Event    │ │ Work  │ │ Analytics │
            │ Store    │ │ flow  │ │ Pipeline  │
            │(Postgres)│ │Engine │ │           │
            └──────────┘ └───────┘ └───────────┘
```

### Key Components

1. **Kafka Cluster**: 3-broker cluster with high availability
2. **Schema Registry**: Avro schema management
3. **Event Publisher**: Circuit breaker, DLQ, batch publishing
4. **Event Consumer**: Parallel processing, monitoring
5. **Event Store**: PostgreSQL-based event sourcing
6. **Workflow Engine**: Saga pattern for distributed transactions
7. **Monitoring**: Kafka UI, Prometheus, Grafana

## Infrastructure Setup

### Docker Compose

The infrastructure is defined in `docker-compose.yml`:

```yaml
# 3 Kafka Brokers
kafka-1:
  ports: ["9092:9092"]
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_DEFAULT_REPLICATION_FACTOR: 3
    KAFKA_MIN_INSYNC_REPLICAS: 2

kafka-2:
  ports: ["9094:9094"]

kafka-3:
  ports: ["9095:9095"]

# Schema Registry (Avro)
schema-registry:
  ports: ["8081:8081"]

# Kafka UI (Monitoring)
kafka-ui:
  ports: ["8090:8080"]
```

### Starting the Infrastructure

```bash
# Start all services
docker-compose up -d

# Verify Kafka cluster
docker-compose ps kafka-1 kafka-2 kafka-3

# Access Kafka UI
open http://localhost:8090
```

### Topic Configuration

Topics are auto-created with the following settings:

- **Partitions**: 12 (for high throughput)
- **Replication Factor**: 3 (for durability)
- **Min In-Sync Replicas**: 2 (for consistency)
- **Retention**: 30-90 days based on domain

## Event Publishing

### Basic Event Publishing

```python
from shared.events import publish_event, EventType

# Publish a patient created event
event_id = await publish_event(
    event_type=EventType.PATIENT_CREATED,
    tenant_id=str(tenant_id),
    payload={
        "patient_id": str(patient.id),
        "name": f"{patient.first_name} {patient.last_name}",
        "date_of_birth": str(patient.date_of_birth),
    },
    source_service="prm-service",
    source_user_id=current_user.id,
)
```

### Batch Publishing (High Throughput)

```python
from shared.events import BatchEventPublisher

# Create batch publisher
publisher = BatchEventPublisher(
    bootstrap_servers="kafka-1:9093,kafka-2:9093,kafka-3:9093",
    batch_size=100,
    flush_interval=5.0,
)

await publisher.start_auto_flush()

# Add events to batch
for patient in patients:
    await publisher.add_event(
        event_type=EventType.PATIENT_CREATED,
        tenant_id=str(tenant_id),
        payload={"patient_id": str(patient.id)},
    )

# Flush remaining events
await publisher.flush()
await publisher.stop()
```

### Circuit Breaker Pattern

```python
from shared.events import CircuitBreaker, get_publisher

publisher = get_publisher()
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
)

try:
    result = circuit_breaker.call(
        publisher.publish,
        event_type=EventType.PATIENT_CREATED,
        tenant_id=tenant_id,
        payload=payload,
    )
except CircuitBreakerOpenError:
    logger.warning("Circuit breaker is open, using fallback")
    # Use fallback mechanism
```

## Event Consumption

### Basic Event Consumer

```python
from shared.events import EventConsumer, Event, EventType

# Create consumer
consumer = EventConsumer(
    group_id="prm-service-consumer",
    topics=["healthtech.patient.events"],
)

# Register event handlers
async def handle_patient_created(event: Event):
    patient_id = event.payload["patient_id"]
    logger.info(f"Handling patient created: {patient_id}")
    # Process event

consumer.register_handler(EventType.PATIENT_CREATED, handle_patient_created)

# Start consuming
await consumer.start()
```

### Service-Specific Consumer

```python
from shared.events import create_consumer_for_service

# Create consumer for service
consumer = create_consumer_for_service(
    service_name="prm-service",
    topics=["healthtech.patient.events", "healthtech.appointment.events"],
)

# Register handlers
consumer.register_handler(EventType.PATIENT_CREATED, handle_patient_created)
consumer.register_handler(EventType.APPOINTMENT_CREATED, handle_appointment_created)

await consumer.start()
```

## Event Store & Event Sourcing

### Appending Events

```python
from shared.events import EventStore
from shared.database.connection import get_db_session

with get_db_session() as db:
    event_store = EventStore(db)

    # Append event to aggregate
    event_id = await event_store.append_event(
        aggregate_type="Patient",
        aggregate_id=patient_id,
        event_type=EventType.PATIENT_CREATED,
        event_data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        },
        tenant_id=str(tenant_id),
        version=1,  # Expected version (optimistic concurrency)
    )
```

### Rebuilding Aggregates

```python
from shared.events import PatientAggregate

# Rebuild patient aggregate from events
patient_aggregate = event_store.rebuild_aggregate(
    aggregate_id=patient_id,
    aggregate_class=PatientAggregate,
)

# Current state of patient
print(patient_aggregate.name, patient_aggregate.email)
```

### Snapshots for Performance

```python
# Save snapshot at current version
await event_store.save_snapshot(
    aggregate_type="Patient",
    aggregate_id=patient_id,
    state=patient_aggregate.to_snapshot(),
    version=patient_aggregate.version,
    tenant_id=str(tenant_id),
)

# Load from snapshot (much faster)
snapshot = event_store.get_snapshot(patient_id)
patient = PatientAggregate.from_snapshot(snapshot["state"])
```

### Event Replay

```python
# Replay events for analysis or rebuilding projections
async def event_handler(event: Event):
    # Process event
    print(f"Replaying: {event.event_type.value}")

await event_store.replay_events(
    tenant_id=str(tenant_id),
    event_handler=event_handler,
    from_date=datetime(2024, 1, 1),
    event_types=[EventType.PATIENT_CREATED, EventType.PATIENT_UPDATED],
)
```

## Workflow Engine & Saga Pattern

### Defining a Workflow

```python
from shared.events import WorkflowDefinition, WorkflowStep

workflow = WorkflowDefinition(
    workflow_id="patient-admission",
    name="Patient Admission Workflow",
    description="Complete patient admission process",
    steps=[
        WorkflowStep(
            step_id="check-bed-availability",
            name="Check Bed Availability",
            action="check_beds",
            compensation_action="release_bed_hold",
            timeout_seconds=30,
        ),
        WorkflowStep(
            step_id="create-admission",
            name="Create Admission Record",
            action="create_admission",
            compensation_action="cancel_admission",
        ),
        WorkflowStep(
            step_id="assign-bed",
            name="Assign Bed to Patient",
            action="assign_bed",
            compensation_action="unassign_bed",
        ),
        WorkflowStep(
            step_id="notify-ward",
            name="Notify Ward Staff",
            action="notify_ward_staff",
        ),
    ],
    enable_compensation=True,  # Enable saga pattern
)
```

### Registering Workflow

```python
from shared.events import get_workflow_engine

engine = get_workflow_engine()
engine.register_workflow(workflow)

# Register action handlers
async def check_beds(context: Dict, input_data: Dict) -> Dict:
    # Check bed availability
    available_beds = get_available_beds(input_data["ward_id"])
    if not available_beds:
        raise Exception("No beds available")
    return {"bed_id": available_beds[0].id}

async def create_admission(context: Dict, input_data: Dict) -> Dict:
    # Create admission record
    admission = create_admission_record(
        patient_id=context["patient_id"],
        ward_id=context["ward_id"],
    )
    return {"admission_id": admission.id}

# Register compensation handlers
async def cancel_admission(context: Dict, output_data: Dict):
    # Rollback admission creation
    admission_id = output_data["admission_id"]
    delete_admission(admission_id)

engine.register_action("check_beds", check_beds)
engine.register_action("create_admission", create_admission)
engine.register_compensation("cancel_admission", cancel_admission)
```

### Starting a Workflow

```python
# Start workflow instance
instance_id = await engine.start_workflow(
    workflow_id="patient-admission",
    tenant_id=str(tenant_id),
    context={
        "patient_id": str(patient_id),
        "ward_id": str(ward_id),
    },
)

# Check workflow status
state = engine.get_instance_state(instance_id)
print(f"Workflow state: {state}")
```

### Saga Pattern - Automatic Compensation

If any step fails, the workflow engine automatically:

1. Stops forward execution
2. Executes compensation actions in reverse order
3. Rolls back completed steps
4. Publishes compensation events

```python
# Example: Step 3 fails
# Engine automatically:
# 1. Calls unassign_bed() for step 3
# 2. Calls cancel_admission() for step 2
# 3. Calls release_bed_hold() for step 1
# 4. Marks workflow as COMPENSATED
```

## Circuit Breaker & Resilience

### Circuit Breaker States

```
CLOSED ──(failures > threshold)──▶ OPEN
   ▲                                  │
   │                                  │ (timeout)
   │                                  ▼
   └─────(successes)────────── HALF_OPEN
```

### Configuration

```python
from shared.events import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes in HALF_OPEN
    timeout=60.0,            # Try HALF_OPEN after 60 seconds
    half_open_max_requests=3, # Max concurrent requests in HALF_OPEN
)
```

## Dead Letter Queue

### Failed Event Handling

```python
from shared.events import get_dlq_handler

dlq = get_dlq_handler()

try:
    # Attempt to process event
    await process_event(event)
except Exception as e:
    # Send to DLQ
    dlq.send_to_dlq(
        event=event,
        error=e,
        retry_count=0,
        metadata={"service": "prm-service"},
    )
```

### DLQ Topics

Failed events are routed to DLQ topics:

- `healthtech.dlq.patient` - Patient event failures
- `healthtech.dlq.appointment` - Appointment event failures
- `healthtech.dlq.clinical` - Clinical event failures

## Best Practices

### Event Design

1. **Immutable Events**: Events should never be modified after publishing
2. **Schema Versioning**: Use version field for schema evolution
3. **Idempotent Handlers**: Handlers should be idempotent (safe to retry)
4. **Correlation IDs**: Always include correlation ID for tracing

### Performance

1. **Batch Publishing**: Use batch publisher for bulk operations (>100 events)
2. **Partitioning**: Use tenant_id as partition key for balanced load
3. **Snapshots**: Create snapshots every 100 events for aggregates
4. **Consumer Groups**: Use separate consumer groups per service

### Reliability

1. **Acknowledgment**: Use `acks=all` for critical events
2. **Replication**: Maintain replication factor of 3
3. **DLQ**: Always send failed events to DLQ for analysis
4. **Circuit Breaker**: Wrap external service calls with circuit breaker

### Monitoring

1. **Consumer Lag**: Alert if lag > 1000 messages
2. **Error Rate**: Alert if error rate > 1%
3. **DLQ Size**: Alert if DLQ size > 100 messages
4. **Circuit Breaker**: Alert when circuit opens

## Monitoring & Observability

### Kafka UI

Access Kafka UI at: `http://localhost:8090`

Features:
- View all topics and partitions
- Monitor consumer groups and lag
- View message contents
- Schema registry management

### Metrics

Key metrics to monitor:

```python
# Publisher Metrics
- event_published_total
- event_publish_duration_seconds
- event_publish_errors_total

# Consumer Metrics
- event_consumed_total
- event_processing_duration_seconds
- consumer_lag_messages

# Circuit Breaker Metrics
- circuit_breaker_state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
- circuit_breaker_failures_total
- circuit_breaker_successes_total

# DLQ Metrics
- dlq_messages_total
- dlq_retries_total
```

### Example Queries

```promql
# Consumer lag by service
sum(consumer_lag_messages) by (service)

# Event publishing rate
rate(event_published_total[5m])

# Error rate
rate(event_publish_errors_total[5m]) / rate(event_published_total[5m])

# Circuit breaker status
circuit_breaker_state{service="prm-service"}
```

## Database Schema

The event store uses the following tables:

```sql
-- Event Store
CREATE TABLE stored_events (
    event_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    version INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE (aggregate_id, version)
);

-- Snapshots
CREATE TABLE aggregate_snapshots (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    version INTEGER NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Failed Events (DLQ)
CREATE TABLE failed_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_payload JSONB NOT NULL,
    error_type VARCHAR(255) NOT NULL,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    failed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    retried BOOLEAN NOT NULL DEFAULT FALSE,
    resolved BOOLEAN NOT NULL DEFAULT FALSE
);
```

## Migration Guide

To create the database tables:

```bash
# Generate migration
alembic revision --autogenerate -m "Add event store tables"

# Run migration
alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Consumer Lag Growing**
   - Solution: Scale up consumers or optimize handlers

2. **Circuit Breaker Always Open**
   - Solution: Check service health, increase timeout

3. **High DLQ Size**
   - Solution: Investigate failed events, fix bugs, replay

4. **Kafka Connection Errors**
   - Solution: Verify bootstrap servers, check network

### Debug Commands

```bash
# View Kafka topics
docker-compose exec kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Consumer group lag
docker-compose exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group prm-service-consumer

# View messages
docker-compose exec kafka-1 kafka-console-consumer --bootstrap-server localhost:9092 --topic healthtech.patient.events --from-beginning
```

## Next Steps

1. Implement event analytics pipeline (Elasticsearch)
2. Add real-time dashboards (Grafana)
3. Implement event versioning and migration
4. Add comprehensive tests (unit, integration, chaos)
5. Document all domain events in event catalog
6. Implement event replay UI for operations

## References

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
