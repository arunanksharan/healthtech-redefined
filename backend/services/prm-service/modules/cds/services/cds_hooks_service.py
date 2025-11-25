"""
CDS Hooks Service

Implements CDS Hooks 1.0 specification for EHR integration,
service registry, and card management.

EPIC-020: Clinical Decision Support
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from modules.cds.models import (
    CDSService,
    CDSHookInvocation,
    CDSCard,
    CDSHookType,
    CDSCardType,
)
from modules.cds.schemas import (
    CDSServiceCreate,
    CDSServiceUpdate,
    CDSHookRequest,
    CDSHookResponse,
    CDSCardResponse,
    CDSSuggestion,
    CDSLink,
)


class CDSHooksService:
    """Service for CDS Hooks implementation."""

    # Default timeout for external service calls
    DEFAULT_TIMEOUT_MS = 5000

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # Service Registry Methods

    async def register_service(
        self,
        data: CDSServiceCreate,
    ) -> CDSService:
        """Register a new CDS service."""
        service = CDSService(
            tenant_id=self.tenant_id,
            service_id=data.service_id,
            name=data.name,
            description=data.description,
            hook=data.hook,
            endpoint_url=data.endpoint_url,
            is_internal=data.is_internal,
            auth_type=data.auth_type,
            prefetch_templates=data.prefetch_templates,
            timeout_ms=data.timeout_ms,
            priority=data.priority,
        )
        self.db.add(service)
        await self.db.flush()
        return service

    async def get_service(self, service_id: str) -> Optional[CDSService]:
        """Get a CDS service by service ID."""
        query = select(CDSService).where(
            and_(
                CDSService.tenant_id == self.tenant_id,
                CDSService.service_id == service_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_service_by_uuid(self, uuid: UUID) -> Optional[CDSService]:
        """Get a CDS service by UUID."""
        query = select(CDSService).where(
            and_(
                CDSService.tenant_id == self.tenant_id,
                CDSService.id == uuid,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_service(
        self,
        service_id: str,
        data: CDSServiceUpdate,
    ) -> Optional[CDSService]:
        """Update a CDS service."""
        service = await self.get_service(service_id)
        if not service:
            return None

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(service, key):
                setattr(service, key, value)

        await self.db.flush()
        return service

    async def list_services(
        self,
        hook: Optional[CDSHookType] = None,
        is_enabled: bool = True,
        is_internal: Optional[bool] = None,
    ) -> List[CDSService]:
        """List registered CDS services."""
        query = select(CDSService).where(
            and_(
                CDSService.tenant_id == self.tenant_id,
                CDSService.is_enabled == is_enabled,
            )
        )

        if hook:
            query = query.where(CDSService.hook == hook)

        if is_internal is not None:
            query = query.where(CDSService.is_internal == is_internal)

        query = query.order_by(CDSService.priority)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_service(self, service_id: str) -> bool:
        """Delete a CDS service."""
        service = await self.get_service(service_id)
        if not service:
            return False

        await self.db.delete(service)
        await self.db.flush()
        return True

    # Hook Invocation Methods

    async def invoke_hook(
        self,
        hook_type: CDSHookType,
        context: Dict[str, Any],
        patient_id: UUID,
        provider_id: Optional[UUID] = None,
        encounter_id: Optional[UUID] = None,
        prefetch_data: Optional[Dict[str, Any]] = None,
    ) -> CDSHookResponse:
        """
        Invoke a CDS hook and collect responses from all registered services.

        Args:
            hook_type: Type of hook being invoked
            context: Hook context data
            patient_id: Patient ID
            provider_id: Provider ID
            encounter_id: Encounter ID
            prefetch_data: Pre-fetched FHIR data
        """
        # Get all services for this hook
        services = await self.list_services(hook=hook_type, is_enabled=True)

        # Create invocation record
        hook_instance = str(uuid4())
        invocation = CDSHookInvocation(
            tenant_id=self.tenant_id,
            hook_type=hook_type,
            hook_instance=hook_instance,
            patient_id=patient_id,
            encounter_id=encounter_id,
            provider_id=provider_id,
            request_context=context,
            prefetch_data=prefetch_data or {},
            services_invoked=[s.service_id for s in services],
        )
        self.db.add(invocation)
        await self.db.flush()

        # Prepare hook request
        hook_request = CDSHookRequest(
            hook=hook_type.value,
            hookInstance=hook_instance,
            context=context,
            prefetch=prefetch_data,
        )

        # Invoke all services and collect cards
        all_cards = []
        error_services = []
        start_time = datetime.utcnow()

        for service in services:
            try:
                cards = await self._invoke_service(service, hook_request, invocation.id)
                all_cards.extend(cards)
            except Exception as e:
                error_services.append(service.service_id)
                # Update service health
                service.failure_count = (service.failure_count or 0) + 1
                if service.failure_count >= 5:
                    service.is_healthy = False

        # Update invocation record
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        invocation.total_cards_returned = len(all_cards)
        invocation.response_time_ms = int(response_time)
        invocation.had_errors = len(error_services) > 0
        invocation.error_services = error_services

        await self.db.flush()

        # Sort cards by indicator severity
        severity_order = {
            CDSCardType.CRITICAL: 0,
            CDSCardType.WARNING: 1,
            CDSCardType.INFO: 2,
            CDSCardType.SUCCESS: 3,
        }
        all_cards.sort(key=lambda c: severity_order.get(CDSCardType(c.indicator), 99))

        return CDSHookResponse(cards=all_cards)

    async def _invoke_service(
        self,
        service: CDSService,
        request: CDSHookRequest,
        invocation_id: UUID,
    ) -> List[CDSCardResponse]:
        """Invoke a single CDS service."""
        cards = []

        if service.is_internal:
            # Handle internal services
            cards = await self._invoke_internal_service(service, request)
        else:
            # Call external service
            cards = await self._invoke_external_service(service, request)

        # Store cards
        for card in cards:
            card_record = CDSCard(
                tenant_id=self.tenant_id,
                invocation_id=invocation_id,
                service_id=service.service_id,
                uuid=card.uuid,
                summary=card.summary,
                detail=card.detail,
                indicator=CDSCardType(card.indicator),
                source_label=card.source.get("label") if card.source else None,
                source_url=card.source.get("url") if card.source else None,
                suggestions=[s.dict() for s in card.suggestions],
                links=[l.dict() for l in card.links],
                selection_behavior=card.selectionBehavior,
            )
            self.db.add(card_record)

        # Update service stats
        service.total_invocations = (service.total_invocations or 0) + 1
        service.last_health_check = datetime.utcnow()
        service.is_healthy = True
        service.failure_count = 0

        return cards

    async def _invoke_internal_service(
        self,
        service: CDSService,
        request: CDSHookRequest,
    ) -> List[CDSCardResponse]:
        """Invoke an internal CDS service."""
        # Route to appropriate internal handler based on service_id
        # This would integrate with other CDS services like DrugInteractionService

        cards = []

        if service.service_id == "drug-interaction-check":
            # Example: Generate drug interaction card
            medications = request.context.get("draftOrders", [])
            if medications:
                cards.append(CDSCardResponse(
                    uuid=str(uuid4()),
                    summary="Drug interaction check complete",
                    detail=f"Checked {len(medications)} medications for interactions",
                    indicator="info",
                    source={"label": "Internal CDS", "url": None},
                ))

        elif service.service_id == "care-gap-alert":
            # Example: Generate care gap card
            patient_id = request.context.get("patientId")
            if patient_id:
                cards.append(CDSCardResponse(
                    uuid=str(uuid4()),
                    summary="Care gaps identified",
                    detail="Patient has outstanding preventive care needs",
                    indicator="warning",
                    source={"label": "Quality Measures", "url": None},
                    suggestions=[
                        CDSSuggestion(
                            label="View care gaps",
                            uuid=str(uuid4()),
                            isRecommended=True,
                        )
                    ],
                ))

        return cards

    async def _invoke_external_service(
        self,
        service: CDSService,
        request: CDSHookRequest,
    ) -> List[CDSCardResponse]:
        """Invoke an external CDS service via HTTP."""
        cards = []

        timeout_seconds = (service.timeout_ms or self.DEFAULT_TIMEOUT_MS) / 1000

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            headers = {"Content-Type": "application/json"}

            # Add authentication if configured
            if service.auth_type == "bearer" and service.auth_credentials:
                token = service.auth_credentials.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            response = await client.post(
                service.endpoint_url,
                json=request.dict(),
                headers=headers,
            )
            response.raise_for_status()

            response_data = response.json()
            for card_data in response_data.get("cards", []):
                cards.append(CDSCardResponse(
                    uuid=card_data.get("uuid"),
                    summary=card_data.get("summary", ""),
                    detail=card_data.get("detail"),
                    indicator=card_data.get("indicator", "info"),
                    source=card_data.get("source", {}),
                    suggestions=[
                        CDSSuggestion(**s) for s in card_data.get("suggestions", [])
                    ],
                    links=[
                        CDSLink(**l) for l in card_data.get("links", [])
                    ],
                    selectionBehavior=card_data.get("selectionBehavior"),
                ))

        return cards

    # Card Interaction Methods

    async def record_card_interaction(
        self,
        card_id: UUID,
        was_accepted: Optional[bool] = None,
        suggestion_selected: Optional[str] = None,
        link_clicked: Optional[str] = None,
    ) -> Optional[CDSCard]:
        """Record user interaction with a CDS card."""
        query = select(CDSCard).where(
            and_(
                CDSCard.id == card_id,
                CDSCard.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        card = result.scalar_one_or_none()

        if card:
            card.was_displayed = True
            if was_accepted is not None:
                card.was_accepted = was_accepted
            if suggestion_selected:
                card.suggestion_selected = suggestion_selected
            if link_clicked:
                card.link_clicked = link_clicked
            if was_accepted is False:
                card.dismissed_at = datetime.utcnow()

            await self.db.flush()

        return card

    async def mark_cards_displayed(
        self,
        invocation_id: UUID,
        card_count: int,
    ):
        """Mark that cards were displayed to user."""
        query = select(CDSHookInvocation).where(
            and_(
                CDSHookInvocation.id == invocation_id,
                CDSHookInvocation.tenant_id == self.tenant_id,
            )
        )
        result = await self.db.execute(query)
        invocation = result.scalar_one_or_none()

        if invocation:
            invocation.cards_displayed = card_count
            await self.db.flush()

    # Discovery Endpoint

    async def get_discovery_response(self) -> Dict[str, Any]:
        """Generate CDS Hooks discovery response."""
        services = await self.list_services(is_enabled=True)

        service_list = []
        for service in services:
            service_info = {
                "id": service.service_id,
                "hook": service.hook.value,
                "title": service.name,
                "description": service.description,
            }

            if service.prefetch_templates:
                service_info["prefetch"] = service.prefetch_templates

            service_list.append(service_info)

        return {"services": service_list}

    # Health Check Methods

    async def check_service_health(self, service_id: str) -> Dict[str, Any]:
        """Check health of a CDS service."""
        service = await self.get_service(service_id)
        if not service:
            return {"status": "not_found"}

        if service.is_internal:
            return {
                "status": "healthy",
                "service_id": service_id,
                "is_internal": True,
            }

        # Ping external service
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(service.endpoint_url.rstrip("/") + "/health")
                is_healthy = response.status_code == 200
        except Exception:
            is_healthy = False

        # Update service health
        service.is_healthy = is_healthy
        service.last_health_check = datetime.utcnow()
        if not is_healthy:
            service.failure_count = (service.failure_count or 0) + 1
        else:
            service.failure_count = 0

        await self.db.flush()

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service_id": service_id,
            "is_internal": False,
            "last_check": service.last_health_check.isoformat(),
            "failure_count": service.failure_count,
        }

    async def get_invocation_history(
        self,
        patient_id: Optional[UUID] = None,
        hook_type: Optional[CDSHookType] = None,
        limit: int = 50,
    ) -> List[CDSHookInvocation]:
        """Get hook invocation history."""
        query = select(CDSHookInvocation).where(
            CDSHookInvocation.tenant_id == self.tenant_id
        )

        if patient_id:
            query = query.where(CDSHookInvocation.patient_id == patient_id)

        if hook_type:
            query = query.where(CDSHookInvocation.hook_type == hook_type)

        query = query.order_by(CDSHookInvocation.invoked_at.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
