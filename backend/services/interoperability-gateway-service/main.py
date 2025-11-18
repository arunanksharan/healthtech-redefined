"""
Interoperability Gateway Service
External system integration, FHIR/HL7 message exchange, and data transformation

Port: 8020
Endpoints: 10 (External Systems, Channels, Message Logs, Inbound FHIR/HL7)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
import logging
import os
import json

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

# Import shared models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database.models import (
    Base, ExternalSystem, InteropChannel, MappingProfile, InteropMessageLog,
    Tenant, Patient, FHIRResource
)
from shared.events.publisher import publish_event, EventType

# Import schemas
from schemas import (
    ExternalSystemCreate, ExternalSystemUpdate, ExternalSystemResponse, ExternalSystemListResponse,
    InteropChannelCreate, InteropChannelUpdate, InteropChannelResponse, InteropChannelListResponse,
    MappingProfileCreate, MappingProfileResponse,
    InteropMessageLogResponse, InteropMessageLogListResponse,
    FHIRInboundRequest, FHIRInboundResponse, HL7InboundRequest, HL7InboundResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthtech:healthtech123@localhost:5432/healthtech_db"
)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Interoperability Gateway Service",
    description="External system integration, FHIR/HL7 message exchange, and data transformation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# Dependencies
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Helper Functions ====================

def apply_mapping_profile(
    mapping_profile: MappingProfile,
    source_data: dict
) -> dict:
    """
    Apply mapping rules to transform data

    In production:
    - Full JSONPath/JMESPath expression evaluation
    - Complex transformations (date formatting, code mapping)
    - Validation against target schema

    For now: simplified mapping
    """
    if not mapping_profile or not mapping_profile.mapping_rules:
        return source_data

    mapped_data = {}
    rules = mapping_profile.mapping_rules

    # Simplified mapping - production would use proper JSONPath
    for target_field, source_path in rules.items():
        # Simple field mapping (not full JSONPath)
        if source_path.startswith("$."):
            field_name = source_path[2:]
            if field_name in source_data:
                mapped_data[target_field] = source_data[field_name]
        else:
            mapped_data[target_field] = source_path

    return mapped_data


def parse_hl7_message(hl7_text: str) -> dict:
    """
    Parse HL7v2 message into structured format

    In production:
    - Full HL7v2 parser
    - Segment extraction
    - Field/component/subcomponent parsing

    For now: simplified parsing
    """
    lines = hl7_text.split('\n')
    parsed = {
        "segments": [],
        "message_type": None
    }

    for line in lines:
        if not line.strip():
            continue

        fields = line.split('|')
        if not fields:
            continue

        segment_id = fields[0]
        parsed["segments"].append({
            "id": segment_id,
            "fields": fields[1:] if len(fields) > 1 else []
        })

        # Extract message type from MSH segment
        if segment_id == "MSH" and len(fields) > 8:
            parsed["message_type"] = fields[8]

    return parsed


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "interoperability-gateway-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== External System Endpoints ====================

@app.post("/api/v1/interop/external-systems", response_model=ExternalSystemResponse, status_code=201)
async def create_external_system(
    system_data: ExternalSystemCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new external system

    - Define external EHR, LIS, RIS, or other system
    - Configure authentication and capabilities
    - Publishes EXTERNAL_SYSTEM_REGISTERED event
    """
    try:
        # Check if code already exists for tenant
        existing = db.query(ExternalSystem).filter(
            and_(
                ExternalSystem.tenant_id == system_data.tenant_id,
                ExternalSystem.code == system_data.code
            )
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail=f"External system with code '{system_data.code}' already exists")

        # Create external system
        external_system = ExternalSystem(
            tenant_id=system_data.tenant_id,
            code=system_data.code,
            name=system_data.name,
            system_type=system_data.system_type,
            base_url=system_data.base_url,
            auth_type=system_data.auth_type,
            auth_config=system_data.auth_config,
            fhir_capability=system_data.fhir_capability,
            hl7v2_capability=system_data.hl7v2_capability,
            is_active=system_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(external_system)
        db.commit()
        db.refresh(external_system)

        # Publish event
        await publish_event(
            EventType.EXTERNAL_SYSTEM_REGISTERED,
            {
                "system_id": str(external_system.id),
                "tenant_id": str(external_system.tenant_id),
                "code": external_system.code,
                "system_type": external_system.system_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Registered external system: {external_system.code} (ID: {external_system.id})")
        return external_system

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating external system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/interop/external-systems", response_model=ExternalSystemListResponse)
async def list_external_systems(
    tenant_id: Optional[UUID] = Query(None),
    system_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List external systems with filtering

    - Filter by tenant, type, active status
    - Paginated results
    """
    try:
        query = db.query(ExternalSystem)

        if tenant_id:
            query = query.filter(ExternalSystem.tenant_id == tenant_id)
        if system_type:
            query = query.filter(ExternalSystem.system_type == system_type.upper())
        if is_active is not None:
            query = query.filter(ExternalSystem.is_active == is_active)

        total = query.count()
        offset = (page - 1) * page_size
        systems = query.order_by(desc(ExternalSystem.created_at)).offset(offset).limit(page_size).all()

        return ExternalSystemListResponse(
            total=total,
            systems=systems,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing external systems: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/interop/external-systems/{system_id}", response_model=ExternalSystemResponse)
async def get_external_system(
    system_id: UUID,
    db: Session = Depends(get_db)
):
    """Get external system by ID"""
    try:
        system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
        if not system:
            raise HTTPException(status_code=404, detail="External system not found")
        return system
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching external system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/interop/external-systems/{system_id}", response_model=ExternalSystemResponse)
async def update_external_system(
    system_id: UUID,
    system_update: ExternalSystemUpdate,
    db: Session = Depends(get_db)
):
    """Update external system configuration"""
    try:
        system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
        if not system:
            raise HTTPException(status_code=404, detail="External system not found")

        update_data = system_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(system, field, value)

        system.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(system)

        logger.info(f"Updated external system: {system.code} (ID: {system.id})")
        return system

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating external system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Interop Channel Endpoints ====================

@app.post("/api/v1/interop/channels", response_model=InteropChannelResponse, status_code=201)
async def create_interop_channel(
    channel_data: InteropChannelCreate,
    db: Session = Depends(get_db)
):
    """
    Create an interoperability channel

    - Configure FHIR REST, HL7 TCP, webhook, or SFTP channel
    - Define resource scope and direction
    - Link to mapping profile for transformations
    """
    try:
        # Validate external system exists
        external_system = db.query(ExternalSystem).filter(
            ExternalSystem.id == channel_data.external_system_id
        ).first()
        if not external_system:
            raise HTTPException(status_code=404, detail="External system not found")

        # Validate mapping profile if provided
        if channel_data.mapping_profile_id:
            mapping_profile = db.query(MappingProfile).filter(
                MappingProfile.id == channel_data.mapping_profile_id
            ).first()
            if not mapping_profile:
                raise HTTPException(status_code=404, detail="Mapping profile not found")

        channel = InteropChannel(
            tenant_id=channel_data.tenant_id,
            external_system_id=channel_data.external_system_id,
            channel_type=channel_data.channel_type,
            direction=channel_data.direction,
            resource_scope=channel_data.resource_scope,
            mapping_profile_id=channel_data.mapping_profile_id,
            is_active=channel_data.is_active,
            config=channel_data.config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(channel)
        db.commit()
        db.refresh(channel)

        logger.info(f"Created interop channel: {channel.channel_type} for system {external_system.code}")
        return channel

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating interop channel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/interop/channels", response_model=InteropChannelListResponse)
async def list_interop_channels(
    tenant_id: Optional[UUID] = Query(None),
    external_system_id: Optional[UUID] = Query(None),
    direction: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List interop channels with filtering"""
    try:
        query = db.query(InteropChannel)

        if tenant_id:
            query = query.filter(InteropChannel.tenant_id == tenant_id)
        if external_system_id:
            query = query.filter(InteropChannel.external_system_id == external_system_id)
        if direction:
            query = query.filter(InteropChannel.direction == direction.lower())
        if is_active is not None:
            query = query.filter(InteropChannel.is_active == is_active)

        total = query.count()
        offset = (page - 1) * page_size
        channels = query.order_by(desc(InteropChannel.created_at)).offset(offset).limit(page_size).all()

        return InteropChannelListResponse(
            total=total,
            channels=channels,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing interop channels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/interop/channels/{channel_id}", response_model=InteropChannelResponse)
async def update_interop_channel(
    channel_id: UUID,
    channel_update: InteropChannelUpdate,
    db: Session = Depends(get_db)
):
    """Update interop channel configuration"""
    try:
        channel = db.query(InteropChannel).filter(InteropChannel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Interop channel not found")

        update_data = channel_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(channel, field, value)

        channel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(channel)

        logger.info(f"Updated interop channel: {channel.id}")
        return channel

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating interop channel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Message Log Endpoints ====================

@app.get("/api/v1/interop/messages", response_model=InteropMessageLogListResponse)
async def list_interop_messages(
    tenant_id: Optional[UUID] = Query(None),
    channel_id: Optional[UUID] = Query(None),
    direction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List interop message logs with filtering

    - Track all FHIR/HL7 messages (inbound/outbound)
    - Filter by channel, direction, status, time range
    - Used for monitoring and troubleshooting
    """
    try:
        query = db.query(InteropMessageLog)

        if tenant_id:
            query = query.filter(InteropMessageLog.tenant_id == tenant_id)
        if channel_id:
            query = query.filter(InteropMessageLog.channel_id == channel_id)
        if direction:
            query = query.filter(InteropMessageLog.direction == direction.lower())
        if status:
            query = query.filter(InteropMessageLog.status == status.lower())
        if from_date:
            query = query.filter(InteropMessageLog.occurred_at >= from_date)
        if to_date:
            query = query.filter(InteropMessageLog.occurred_at <= to_date)

        total = query.count()
        offset = (page - 1) * page_size
        messages = query.order_by(desc(InteropMessageLog.occurred_at)).offset(offset).limit(page_size).all()

        return InteropMessageLogListResponse(
            total=total,
            messages=messages,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing interop messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Inbound Message Endpoints ====================

@app.post("/api/v1/interop/fhir/{tenant_code}/{resource_type}", response_model=FHIRInboundResponse)
async def receive_fhir_resource(
    tenant_code: str = Path(..., description="Tenant code"),
    resource_type: str = Path(..., description="FHIR resource type"),
    fhir_request: FHIRInboundRequest = None,
    db: Session = Depends(get_db)
):
    """
    Receive inbound FHIR resource from external system

    - Identify external system by auth/headers
    - Apply mapping profile to transform to internal format
    - Create/update FHIR resource in internal store
    - Publish events for downstream processing
    """
    try:
        # Find tenant
        tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # TODO: Identify external system from auth headers
        # For now, use first active external system
        external_system = db.query(ExternalSystem).filter(
            and_(
                ExternalSystem.tenant_id == tenant.id,
                ExternalSystem.is_active == True
            )
        ).first()

        if not external_system:
            raise HTTPException(status_code=400, detail="No active external system configured")

        # Find appropriate channel
        channel = db.query(InteropChannel).filter(
            and_(
                InteropChannel.external_system_id == external_system.id,
                InteropChannel.direction.in_(["inbound", "bidirectional"]),
                InteropChannel.is_active == True
            )
        ).first()

        if not channel:
            raise HTTPException(status_code=400, detail="No active inbound channel configured")

        message_log_id = uuid4()
        occurred_at = datetime.utcnow()

        # Create message log
        message_log = InteropMessageLog(
            id=message_log_id,
            tenant_id=tenant.id,
            channel_id=channel.id,
            external_system_id=external_system.id,
            direction="inbound",
            message_type=f"FHIR.{resource_type}",
            correlation_id=fhir_request.correlation_id,
            raw_payload=json.dumps(fhir_request.resource)[:10000],  # Truncate if too large
            status="received",
            occurred_at=occurred_at,
            created_at=datetime.utcnow()
        )
        db.add(message_log)

        # Apply mapping if profile exists
        resource_data = fhir_request.resource
        if channel.mapping_profile_id:
            mapping_profile = db.query(MappingProfile).filter(
                MappingProfile.id == channel.mapping_profile_id
            ).first()
            if mapping_profile:
                resource_data = apply_mapping_profile(mapping_profile, resource_data)
                message_log.status = "mapped"

        # Create FHIR resource in internal store
        # TODO: Actual FHIR resource creation logic
        mapped_resource_id = str(uuid4())
        message_log.mapped_resource_type = resource_type
        message_log.mapped_resource_id = mapped_resource_id
        message_log.status = "completed"

        db.commit()

        logger.info(f"Received FHIR {resource_type} from {external_system.code}")

        return FHIRInboundResponse(
            message_log_id=message_log_id,
            status="completed",
            mapped_resource_id=mapped_resource_id,
            mapped_resource_type=resource_type
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error receiving FHIR resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/interop/hl7/{tenant_code}", response_model=HL7InboundResponse)
async def receive_hl7_message(
    tenant_code: str = Path(..., description="Tenant code"),
    hl7_request: HL7InboundRequest = None,
    db: Session = Depends(get_db)
):
    """
    Receive inbound HL7v2 message from external system

    - Parse HL7 message
    - Apply mapping to internal format
    - Create events/resources
    - Return ACK message
    """
    try:
        # Find tenant
        tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Parse HL7 message
        parsed_hl7 = parse_hl7_message(hl7_request.message)

        # Find external system
        external_system = db.query(ExternalSystem).filter(
            and_(
                ExternalSystem.tenant_id == tenant.id,
                ExternalSystem.is_active == True
            )
        ).first()

        if not external_system:
            raise HTTPException(status_code=400, detail="No active external system configured")

        # Find channel
        channel = db.query(InteropChannel).filter(
            and_(
                InteropChannel.external_system_id == external_system.id,
                InteropChannel.channel_type == "HL7V2_TCP",
                InteropChannel.is_active == True
            )
        ).first()

        message_log_id = uuid4()
        occurred_at = datetime.utcnow()

        # Create message log
        message_log = InteropMessageLog(
            id=message_log_id,
            tenant_id=tenant.id,
            channel_id=channel.id if channel else None,
            external_system_id=external_system.id,
            direction="inbound",
            message_type=f"HL7.{parsed_hl7.get('message_type', 'UNKNOWN')}",
            correlation_id=hl7_request.correlation_id,
            raw_payload=hl7_request.message[:10000],
            status="parsed",
            occurred_at=occurred_at,
            created_at=datetime.utcnow()
        )
        db.add(message_log)

        # TODO: Process HL7 message segments and create internal resources
        message_log.status = "completed"

        db.commit()

        # Generate ACK
        ack_message = f"MSH|^~\\&|HEALTHTECH|HIS|{external_system.code}|EXTERNAL|{datetime.utcnow().strftime('%Y%m%d%H%M%S')}||ACK|{hl7_request.correlation_id}|P|2.5\nMSA|AA|{hl7_request.correlation_id}"

        logger.info(f"Received HL7 message type {parsed_hl7.get('message_type')} from {external_system.code}")

        return HL7InboundResponse(
            message_log_id=message_log_id,
            status="completed",
            message_type=parsed_hl7.get('message_type'),
            ack_message=ack_message
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error receiving HL7 message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)
