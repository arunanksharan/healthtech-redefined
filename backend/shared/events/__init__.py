"""
Event system package
Provides event publishing and consumption infrastructure
"""
from .publisher import EventPublisher, publish_event, get_publisher
from .consumer import EventConsumer, create_consumer_for_service
from .types import EventType, Event
from .batch_publisher import BatchEventPublisher
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from .dlq_handler import DLQHandler, get_dlq_handler
from .event_store import EventStore, ConcurrencyError, PatientAggregate
from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStep,
    WorkflowState,
    StepState,
    get_workflow_engine,
)

__all__ = [
    # Core event system
    "EventPublisher",
    "publish_event",
    "get_publisher",
    "EventConsumer",
    "create_consumer_for_service",
    "EventType",
    "Event",
    # Batch publishing
    "BatchEventPublisher",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    # Dead letter queue
    "DLQHandler",
    "get_dlq_handler",
    # Event store
    "EventStore",
    "ConcurrencyError",
    "PatientAggregate",
    # Workflow engine
    "WorkflowEngine",
    "WorkflowDefinition",
    "WorkflowInstance",
    "WorkflowStep",
    "WorkflowState",
    "StepState",
    "get_workflow_engine",
]
