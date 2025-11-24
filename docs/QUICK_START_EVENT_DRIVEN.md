# Quick Start: Event-Driven Architecture

This guide will help you get started with the event-driven architecture in under 10 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- Access to the repository

## Step 1: Start Infrastructure (2 minutes)

```bash
# Navigate to project root
cd /path/to/healthtech-redefined

# Start all infrastructure services
docker-compose up -d kafka-1 kafka-2 kafka-3 schema-registry kafka-ui zookeeper postgres redis

# Verify Kafka cluster is running
docker-compose ps kafka-1 kafka-2 kafka-3

# Expected output: All 3 brokers should be "Up"
```

## Step 2: Access Kafka UI (30 seconds)

Open your browser and navigate to:
```
http://localhost:8090
```

You should see:
- Kafka cluster status
- Available topics
- Consumer groups
- Schema registry

## Step 3: Run Database Migrations (1 minute)

```bash
cd backend

# Apply migrations for event store tables
alembic upgrade head

# Verify tables were created
psql -h localhost -U postgres -d healthtech -c "\dt"
# Look for: stored_events, aggregate_snapshots, failed_events
```

## Step 4: Publish Your First Event (2 minutes)

Create a test script `test_event.py`:

```python
import asyncio
from shared.events import publish_event, EventType

async def main():
    # Publish a test event
    event_id = await publish_event(
        event_type=EventType.PATIENT_CREATED,
        tenant_id="test-hospital",
        payload={
            "patient_id": "PAT-123",
            "name": "John Doe",
            "email": "john.doe@example.com"
        },
        source_service="test-script",
    )

    print(f"✅ Event published successfully! Event ID: {event_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_event.py
```

## Step 5: View Event in Kafka UI (1 minute)

1. Go to Kafka UI: http://localhost:8090
2. Click on "Topics"
3. Find topic: `healthtech.patient.events`
4. Click "Messages"
5. You should see your event!

## Step 6: Create a Consumer (2 minutes)

Create `test_consumer.py`:

```python
import asyncio
from shared.events import EventConsumer, Event, EventType
from loguru import logger

async def handle_patient_created(event: Event):
    """Handle patient created event"""
    patient_id = event.payload["patient_id"]
    name = event.payload["name"]
    logger.info(f"📬 Received: Patient {name} ({patient_id}) was created!")

async def main():
    # Create consumer
    consumer = EventConsumer(
        group_id="test-consumer-group",
        topics=["healthtech.patient.events"],
    )

    # Register handler
    consumer.register_handler(
        EventType.PATIENT_CREATED,
        handle_patient_created,
    )

    logger.info("🎧 Consumer started. Waiting for events...")

    # Start consuming
    await consumer.start()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_consumer.py
```

Leave it running, then in another terminal publish another event (run test_event.py again).
You should see the consumer log the received event!

## Step 7: Try the Event Store (2 minutes)

Create `test_event_store.py`:

```python
import asyncio
from uuid import uuid4
from shared.events import EventStore, EventType, PatientAggregate
from shared.database.connection import get_db_session

async def main():
    with get_db_session() as db:
        event_store = EventStore(db)
        patient_id = uuid4()

        # Append first event
        await event_store.append_event(
            aggregate_type="Patient",
            aggregate_id=patient_id,
            event_type=EventType.PATIENT_CREATED,
            event_data={
                "patient_id": str(patient_id),
                "name": "Jane Smith",
                "email": "jane@example.com",
            },
            tenant_id="test-hospital",
            version=1,
        )

        # Append second event
        await event_store.append_event(
            aggregate_type="Patient",
            aggregate_id=patient_id,
            event_type=EventType.PATIENT_UPDATED,
            event_data={
                "email": "jane.smith@example.com",
            },
            tenant_id="test-hospital",
            version=2,
        )

        # Rebuild aggregate from events
        patient = event_store.rebuild_aggregate(
            aggregate_id=patient_id,
            aggregate_class=PatientAggregate,
        )

        print(f"✅ Patient aggregate rebuilt from events!")
        print(f"   Name: {patient.name}")
        print(f"   Email: {patient.email}")
        print(f"   Version: {patient.version}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_event_store.py
```

## Step 8: Try a Workflow (2 minutes)

Create `test_workflow.py`:

```python
import asyncio
from shared.events import (
    get_workflow_engine,
    WorkflowDefinition,
    WorkflowStep,
)
from loguru import logger

async def main():
    engine = get_workflow_engine()

    # Define a simple workflow
    workflow = WorkflowDefinition(
        workflow_id="hello-workflow",
        name="Hello World Workflow",
        description="Simple test workflow",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Say Hello",
                action="say_hello",
            ),
            WorkflowStep(
                step_id="step2",
                name="Say Goodbye",
                action="say_goodbye",
            ),
        ],
    )

    # Register workflow
    engine.register_workflow(workflow)

    # Register action handlers
    async def say_hello(context, input_data):
        logger.info("👋 Hello from workflow!")
        return {"message": "hello"}

    async def say_goodbye(context, input_data):
        logger.info("👋 Goodbye from workflow!")
        return {"message": "goodbye"}

    engine.register_action("say_hello", say_hello)
    engine.register_action("say_goodbye", say_goodbye)

    # Start workflow
    instance_id = await engine.start_workflow(
        workflow_id="hello-workflow",
        tenant_id="test-hospital",
    )

    logger.info(f"✅ Workflow started! Instance ID: {instance_id}")

    # Wait for completion
    await asyncio.sleep(2)

    # Check state
    state = engine.get_instance_state(instance_id)
    logger.info(f"📊 Workflow state: {state}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_workflow.py
```

## Congratulations! 🎉

You've successfully:
- ✅ Started a 3-broker Kafka cluster
- ✅ Published your first event
- ✅ Created a consumer to handle events
- ✅ Used the event store
- ✅ Ran a workflow with saga pattern

## Next Steps

### Learn More
1. Read the [Event-Driven Architecture Guide](./EVENT_DRIVEN_ARCHITECTURE_GUIDE.md)
2. Browse the [Event Catalog](./EVENT_CATALOG.md)
3. Check the [Implementation Summary](./EPIC-002-IMPLEMENTATION-SUMMARY.md)

### Integration
1. Add event publishing to your service
2. Create consumers for your domain events
3. Define workflows for complex processes

### Production Readiness
1. Add monitoring and alerts
2. Setup backup and disaster recovery
3. Load test your event flows
4. Implement circuit breakers

## Common Issues

### Kafka not starting
```bash
# Check logs
docker-compose logs kafka-1

# Restart Kafka
docker-compose restart kafka-1 kafka-2 kafka-3
```

### Consumer not receiving events
```bash
# Check consumer group lag
docker-compose exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group your-consumer-group
```

### Event Store errors
```bash
# Verify migrations ran
alembic current

# Check table exists
psql -h localhost -U postgres -d healthtech -c "\d stored_events"
```

## Getting Help

- **Documentation**: `docs/` directory
- **Kafka UI**: http://localhost:8090
- **Issues**: GitHub Issues
- **Team Chat**: Platform Team channel

## Clean Up

To stop all services:
```bash
docker-compose down

# To also remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

**Happy Eventing!** 🚀
