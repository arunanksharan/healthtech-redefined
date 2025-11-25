"""
Event-Driven Architecture Package

Comprehensive event infrastructure including:
- Kafka cluster configuration and management
- Event publishing with retry and circuit breaker
- Event consumption with consumer groups
- Event store for event sourcing
- Domain event definitions (400+ events)
- Workflow engine with saga pattern
- Event analytics pipeline
- Dead letter queue handling
- Service integration helpers

EPIC-002: Event-Driven Architecture
"""

# Core event types and schemas
from .types import (
    Event,
    EventType,
    PatientCreatedPayload,
    AppointmentCreatedPayload,
    ConsentWithdrawnPayload,
    OrderCreatedPayload,
    VitalsRecordedPayload,
    ICUAlertCreatedPayload,
)

# Event publishing
from .publisher import (
    EventPublisher,
    publish_event,
    get_publisher,
)

# Batch publishing
from .batch_publisher import BatchEventPublisher

# Event consumption
from .consumer import (
    EventConsumer,
    create_consumer_for_service,
)

# Circuit breaker
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)

# Dead letter queue
from .dlq_handler import (
    DLQHandler,
    get_dlq_handler,
)

# Event store
from .event_store import (
    EventStore,
    ConcurrencyError,
    PatientAggregate,
)

# Workflow engine
from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStep,
    WorkflowState,
    StepState,
    get_workflow_engine,
)

# Analytics consumer
from .analytics_consumer import EventAnalyticsConsumer

# Kafka configuration
from .kafka_config import (
    KafkaClusterManager,
    TopicConfig,
    ProducerConfig,
    ConsumerConfig,
    CompressionType,
    AcksMode,
    IsolationLevel,
    HEALTHCARE_TOPICS,
    get_cluster_manager,
    get_producer_config,
    get_consumer_config,
)

# Service integration
from .service_integration import (
    ServiceEventIntegration,
    ServiceEventConfig,
    ServiceType,
    EventCorrelation,
    TransactionalOutbox,
    PRM_SERVICE_CONFIG,
    FHIR_SERVICE_CONFIG,
    AI_SERVICE_CONFIG,
    BILLING_SERVICE_CONFIG,
    TELEHEALTH_SERVICE_CONFIG,
    create_service_integration,
    get_service_integration,
    get_correlation_context,
    set_correlation_context,
    clear_correlation_context,
    with_correlation,
    on_event,
    publishes,
    publish_with_correlation,
)

__all__ = [
    # Event types
    "Event",
    "EventType",
    "PatientCreatedPayload",
    "AppointmentCreatedPayload",
    "ConsentWithdrawnPayload",
    "OrderCreatedPayload",
    "VitalsRecordedPayload",
    "ICUAlertCreatedPayload",
    # Publisher
    "EventPublisher",
    "publish_event",
    "get_publisher",
    "BatchEventPublisher",
    # Consumer
    "EventConsumer",
    "create_consumer_for_service",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    # DLQ
    "DLQHandler",
    "get_dlq_handler",
    # Event store
    "EventStore",
    "ConcurrencyError",
    "PatientAggregate",
    # Workflow
    "WorkflowEngine",
    "WorkflowDefinition",
    "WorkflowInstance",
    "WorkflowStep",
    "WorkflowState",
    "StepState",
    "get_workflow_engine",
    # Analytics
    "EventAnalyticsConsumer",
    # Kafka config
    "KafkaClusterManager",
    "TopicConfig",
    "ProducerConfig",
    "ConsumerConfig",
    "CompressionType",
    "AcksMode",
    "IsolationLevel",
    "HEALTHCARE_TOPICS",
    "get_cluster_manager",
    "get_producer_config",
    "get_consumer_config",
    # Service integration
    "ServiceEventIntegration",
    "ServiceEventConfig",
    "ServiceType",
    "EventCorrelation",
    "TransactionalOutbox",
    "PRM_SERVICE_CONFIG",
    "FHIR_SERVICE_CONFIG",
    "AI_SERVICE_CONFIG",
    "BILLING_SERVICE_CONFIG",
    "TELEHEALTH_SERVICE_CONFIG",
    "create_service_integration",
    "get_service_integration",
    "get_correlation_context",
    "set_correlation_context",
    "clear_correlation_context",
    "with_correlation",
    "on_event",
    "publishes",
    "publish_with_correlation",
]
