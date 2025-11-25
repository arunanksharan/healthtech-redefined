"""
FHIR Services
Business logic layer for FHIR operations

This package provides comprehensive FHIR R4 functionality:
- FHIRService: Core CRUD operations for FHIR resources
- OperationsService: FHIR operations ($everything, $meta, $document)
- AdvancedSearchService: Advanced search with chaining, includes, modifiers
- BundleService: Transaction and batch bundle processing
- TerminologyService: CodeSystem, ValueSet, and ConceptMap operations
- SubscriptionService: Real-time notifications via webhooks/WebSocket
"""
from .fhir_service import FHIRService
from .search_service import FHIRSearchService
from .advanced_search_service import (
    AdvancedSearchService,
    SearchQueryBuilder,
    SearchParamType,
    SearchModifier,
    SearchPrefix,
)
from .bundle_service import BundleService
from .operations_service import OperationsService
from .terminology_service import TerminologyService, terminology_service
from .subscription_service import (
    SubscriptionService,
    subscription_service,
    Subscription,
    SubscriptionStatus,
    ChannelType,
)

__all__ = [
    # Core services
    "FHIRService",
    "BundleService",
    "OperationsService",
    # Search services
    "FHIRSearchService",
    "AdvancedSearchService",
    "SearchQueryBuilder",
    "SearchParamType",
    "SearchModifier",
    "SearchPrefix",
    # Terminology services
    "TerminologyService",
    "terminology_service",
    # Subscription services
    "SubscriptionService",
    "subscription_service",
    "Subscription",
    "SubscriptionStatus",
    "ChannelType",
]
