"""
Orders Service API
Manages clinical orders for lab, imaging, procedures, and medications
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import logging
import os

from shared.database.connection import get_db
from shared.database.models import Order, Patient, Practitioner, Encounter, Admission
from shared.events.publisher import publish_event
from shared.events.types import EventType
from .schemas import (
    OrderCreate, OrderUpdate, OrderCancel, OrderResponse,
    OrderListResponse, OrderStats, MedicationOrderCreate
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Orders Service",
    description="Manages clinical orders for lab, imaging, procedures, and medications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Helper Functions ====================

async def create_fhir_service_request(
    db: Session,
    order_data: OrderCreate,
    order_id: UUID
) -> str:
    """Create FHIR ServiceRequest for lab/imaging/procedure orders"""
    from shared.database.models import FHIRResource

    fhir_id = f"ServiceRequest/{order_id}"

    # Map order type to FHIR category
    category_map = {
        "lab": {
            "code": "laboratory",
            "display": "Laboratory"
        },
        "imaging": {
            "code": "imaging",
            "display": "Imaging"
        },
        "procedure": {
            "code": "procedure",
            "display": "Procedure"
        }
    }

    category = category_map.get(order_data.order_type, {"code": "other", "display": "Other"})

    fhir_service_request = {
        "resourceType": "ServiceRequest",
        "id": str(order_id),
        "status": "active",
        "intent": "order",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/servicerequest-category",
                        "code": category["code"],
                        "display": category["display"]
                    }
                ]
            }
        ],
        "priority": order_data.priority,
        "code": {
            "text": order_data.description
        },
        "subject": {
            "reference": f"Patient/{order_data.patient_id}"
        },
        "encounter": {
            "reference": f"Encounter/{order_data.encounter_id}"
        },
        "requester": {
            "reference": f"Practitioner/{order_data.ordering_practitioner_id}"
        },
        "reasonCode": [
            {
                "text": order_data.reason or ""
            }
        ],
        "authoredOn": datetime.utcnow().isoformat()
    }

    # Add coding if code is provided
    if order_data.code:
        fhir_service_request["code"]["coding"] = [
            {
                "system": "http://loinc.org",
                "code": order_data.code,
                "display": order_data.description
            }
        ]

    fhir_resource = FHIRResource(
        tenant_id=order_data.tenant_id,
        resource_type="ServiceRequest",
        fhir_id=fhir_id,
        resource_data=fhir_service_request
    )
    db.add(fhir_resource)

    return fhir_id


async def create_fhir_medication_request(
    db: Session,
    order_data: OrderCreate,
    order_id: UUID
) -> str:
    """Create FHIR MedicationRequest for medication orders"""
    from shared.database.models import FHIRResource

    fhir_id = f"MedicationRequest/{order_id}"

    fhir_medication_request = {
        "resourceType": "MedicationRequest",
        "id": str(order_id),
        "status": "active",
        "intent": "order",
        "priority": order_data.priority,
        "medicationCodeableConcept": {
            "text": order_data.description
        },
        "subject": {
            "reference": f"Patient/{order_data.patient_id}"
        },
        "encounter": {
            "reference": f"Encounter/{order_data.encounter_id}"
        },
        "requester": {
            "reference": f"Practitioner/{order_data.ordering_practitioner_id}"
        },
        "reasonCode": [
            {
                "text": order_data.reason or ""
            }
        ],
        "authoredOn": datetime.utcnow().isoformat()
    }

    fhir_resource = FHIRResource(
        tenant_id=order_data.tenant_id,
        resource_type="MedicationRequest",
        fhir_id=fhir_id,
        resource_data=fhir_medication_request
    )
    db.add(fhir_resource)

    return fhir_id


async def create_fhir_medication_request_detailed(
    db: Session,
    med_order_data: MedicationOrderCreate,
    order_id: UUID
) -> str:
    """Create detailed FHIR MedicationRequest with dosage instructions"""
    from shared.database.models import FHIRResource

    fhir_id = f"MedicationRequest/{order_id}"

    fhir_medication_request = {
        "resourceType": "MedicationRequest",
        "id": str(order_id),
        "status": "active",
        "intent": "order",
        "priority": med_order_data.priority,
        "medicationCodeableConcept": {
            "text": med_order_data.medication_name
        },
        "subject": {
            "reference": f"Patient/{med_order_data.patient_id}"
        },
        "encounter": {
            "reference": f"Encounter/{med_order_data.encounter_id}"
        },
        "requester": {
            "reference": f"Practitioner/{med_order_data.ordering_practitioner_id}"
        },
        "reasonCode": [
            {
                "text": med_order_data.reason or ""
            }
        ],
        "dosageInstruction": [
            {
                "text": f"{med_order_data.dose} {med_order_data.route} {med_order_data.frequency}",
                "route": {
                    "text": med_order_data.route
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": med_order_data.dose
                        }
                    }
                ]
            }
        ],
        "authoredOn": datetime.utcnow().isoformat()
    }

    if med_order_data.duration:
        fhir_medication_request["dosageInstruction"][0]["timing"] = {
            "repeat": {
                "duration": med_order_data.duration
            }
        }

    fhir_resource = FHIRResource(
        tenant_id=med_order_data.tenant_id,
        resource_type="MedicationRequest",
        fhir_id=fhir_id,
        resource_data=fhir_medication_request
    )
    db.add(fhir_resource)

    return fhir_id


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orders-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Order Endpoints ====================

@app.post("/api/v1/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new clinical order

    Order types:
    - lab: Laboratory test
    - imaging: Radiology/imaging study
    - procedure: Medical procedure
    - medication: Medication order

    Creates appropriate FHIR resource:
    - lab/imaging/procedure → ServiceRequest
    - medication → MedicationRequest
    """
    try:
        # Validate patient exists
        patient = db.query(Patient).filter(
            Patient.id == order_data.patient_id,
            Patient.tenant_id == order_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Validate practitioner exists
        practitioner = db.query(Practitioner).filter(
            Practitioner.id == order_data.ordering_practitioner_id,
            Practitioner.tenant_id == order_data.tenant_id
        ).first()

        if not practitioner:
            raise HTTPException(status_code=404, detail="Practitioner not found")

        # Validate encounter exists
        encounter = db.query(Encounter).filter(
            Encounter.id == order_data.encounter_id,
            Encounter.tenant_id == order_data.tenant_id
        ).first()

        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        # Create order record
        order = Order(
            tenant_id=order_data.tenant_id,
            admission_id=order_data.admission_id,
            encounter_id=order_data.encounter_id,
            patient_id=order_data.patient_id,
            ordering_practitioner_id=order_data.ordering_practitioner_id,
            order_type=order_data.order_type.lower(),
            code=order_data.code,
            description=order_data.description,
            status="requested",
            priority=order_data.priority.lower(),
            reason=order_data.reason
        )
        db.add(order)
        db.flush()

        # Create appropriate FHIR resource
        if order_data.order_type.lower() == "medication":
            fhir_id = await create_fhir_medication_request(db, order_data, order.id)
            order.fhir_medication_request_id = fhir_id
        else:
            fhir_id = await create_fhir_service_request(db, order_data, order.id)
            order.fhir_service_request_id = fhir_id

        db.commit()
        db.refresh(order)

        # Publish event
        await publish_event(
            EventType.ORDER_CREATED,
            {
                "order_id": str(order.id),
                "tenant_id": str(order.tenant_id),
                "patient_id": str(order.patient_id),
                "encounter_id": str(order.encounter_id),
                "order_type": order.order_type,
                "priority": order.priority,
                "description": order.description
            }
        )

        logger.info(f"Created order {order.id} for patient {order.patient_id}")
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/orders/medication", response_model=OrderResponse, status_code=201)
async def create_medication_order(
    med_order_data: MedicationOrderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a medication order with detailed dosage instructions

    Specialized endpoint for medication orders with structured dosage data.
    """
    try:
        # Validate patient and practitioner
        patient = db.query(Patient).filter(
            Patient.id == med_order_data.patient_id,
            Patient.tenant_id == med_order_data.tenant_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        practitioner = db.query(Practitioner).filter(
            Practitioner.id == med_order_data.ordering_practitioner_id,
            Practitioner.tenant_id == med_order_data.tenant_id
        ).first()

        if not practitioner:
            raise HTTPException(status_code=404, detail="Practitioner not found")

        # Create description from medication details
        description = (
            f"{med_order_data.medication_name} {med_order_data.dose} "
            f"{med_order_data.route} {med_order_data.frequency}"
        )

        # Create order record
        order = Order(
            tenant_id=med_order_data.tenant_id,
            admission_id=med_order_data.admission_id,
            encounter_id=med_order_data.encounter_id,
            patient_id=med_order_data.patient_id,
            ordering_practitioner_id=med_order_data.ordering_practitioner_id,
            order_type="medication",
            description=description,
            status="requested",
            priority=med_order_data.priority.lower(),
            reason=med_order_data.reason
        )
        db.add(order)
        db.flush()

        # Store structured medication data in metadata
        order.meta_data = {
            "medication_name": med_order_data.medication_name,
            "dose": med_order_data.dose,
            "route": med_order_data.route,
            "frequency": med_order_data.frequency,
            "duration": med_order_data.duration
        }

        # Create detailed FHIR MedicationRequest
        fhir_id = await create_fhir_medication_request_detailed(db, med_order_data, order.id)
        order.fhir_medication_request_id = fhir_id

        db.commit()
        db.refresh(order)

        # Publish event
        await publish_event(
            EventType.ORDER_CREATED,
            {
                "order_id": str(order.id),
                "tenant_id": str(order.tenant_id),
                "patient_id": str(order.patient_id),
                "encounter_id": str(order.encounter_id),
                "order_type": "medication",
                "medication_name": med_order_data.medication_name,
                "priority": order.priority
            }
        )

        logger.info(f"Created medication order {order.id} for patient {order.patient_id}")
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating medication order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get order by ID"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == tenant_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@app.get("/api/v1/orders", response_model=OrderListResponse)
async def list_orders(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    admission_id: Optional[UUID] = Query(None),
    ordering_practitioner_id: Optional[UUID] = Query(None),
    order_type: Optional[str] = Query(None, description="lab, imaging, procedure, medication"),
    status: Optional[str] = Query(None, description="requested, in_progress, completed, cancelled, rejected"),
    priority: Optional[str] = Query(None, description="routine, urgent, stat"),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List orders with filtering

    Filters:
    - patient_id: Filter by patient
    - encounter_id: Filter by encounter
    - admission_id: Filter by admission
    - ordering_practitioner_id: Filter by ordering doctor
    - order_type: Filter by type (lab, imaging, procedure, medication)
    - status: Filter by status
    - priority: Filter by priority
    - from_date / to_date: Filter by creation date range
    """
    query = db.query(Order).filter(Order.tenant_id == tenant_id)

    # Apply filters
    if patient_id:
        query = query.filter(Order.patient_id == patient_id)

    if encounter_id:
        query = query.filter(Order.encounter_id == encounter_id)

    if admission_id:
        query = query.filter(Order.admission_id == admission_id)

    if ordering_practitioner_id:
        query = query.filter(Order.ordering_practitioner_id == ordering_practitioner_id)

    if order_type:
        query = query.filter(Order.order_type == order_type.lower())

    if status:
        query = query.filter(Order.status == status.lower())

    if priority:
        query = query.filter(Order.priority == priority.lower())

    if from_date:
        query = query.filter(Order.created_at >= from_date)

    if to_date:
        query = query.filter(Order.created_at <= to_date)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate pagination metadata
    has_next = (offset + page_size) < total
    has_previous = page > 1

    return OrderListResponse(
        total=total,
        orders=orders,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.patch("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    update_data: OrderUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Update order

    Typically used to update:
    - status (in_progress, completed, cancelled, rejected)
    - external_order_id (from LIS/RIS/Pharmacy)
    - notes
    """
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.tenant_id == tenant_id
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Validate status transitions
        if update_data.status:
            if order.status == "completed":
                raise HTTPException(status_code=400, detail="Cannot update completed order")

            if order.status == "cancelled":
                raise HTTPException(status_code=400, detail="Cannot update cancelled order")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)

        # Store notes in metadata if provided
        if "notes" in update_dict:
            if not order.meta_data:
                order.meta_data = {}
            if "notes" not in order.meta_data:
                order.meta_data["notes"] = []
            order.meta_data["notes"].append({
                "text": update_dict["notes"],
                "timestamp": datetime.utcnow().isoformat()
            })
            update_dict.pop("notes")

        for field, value in update_dict.items():
            setattr(order, field, value)

        order.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        # Publish event
        await publish_event(
            EventType.ORDER_UPDATED,
            {
                "order_id": str(order.id),
                "tenant_id": str(order.tenant_id),
                "patient_id": str(order.patient_id),
                "updated_fields": list(update_dict.keys()),
                "status": order.status
            }
        )

        logger.info(f"Updated order {order.id}")
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    cancel_data: OrderCancel,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Cancel an order"""
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.tenant_id == tenant_id
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status == "completed":
            raise HTTPException(status_code=400, detail="Cannot cancel completed order")

        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Order already cancelled")

        # Cancel order
        order.status = "cancelled"
        order.updated_at = datetime.utcnow()

        # Store cancellation details
        if not order.meta_data:
            order.meta_data = {}

        order.meta_data["cancellation"] = {
            "reason": cancel_data.cancel_reason,
            "cancelled_by": str(cancel_data.cancelled_by_user_id) if cancel_data.cancelled_by_user_id else None,
            "cancelled_at": datetime.utcnow().isoformat()
        }

        db.commit()
        db.refresh(order)

        # Publish event
        await publish_event(
            EventType.ORDER_UPDATED,
            {
                "order_id": str(order.id),
                "tenant_id": str(order.tenant_id),
                "patient_id": str(order.patient_id),
                "status": "cancelled",
                "cancel_reason": cancel_data.cancel_reason
            }
        )

        logger.info(f"Cancelled order {order.id}")
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/orders/stats/overview", response_model=OrderStats)
async def get_order_stats(
    tenant_id: UUID = Query(...),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get order statistics

    Returns:
    - Total orders
    - Pending orders (requested + in_progress)
    - Completed today
    - Order type breakdown
    - Priority breakdown
    - Status breakdown
    """
    query = db.query(Order).filter(Order.tenant_id == tenant_id)

    if from_date:
        query = query.filter(Order.created_at >= from_date)

    if to_date:
        query = query.filter(Order.created_at <= to_date)

    # Total orders
    total_orders = query.count()

    # Pending orders
    pending_orders = query.filter(
        Order.status.in_(["requested", "in_progress"])
    ).count()

    # Completed today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    completed_today = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.status == "completed",
        Order.updated_at >= today_start,
        Order.updated_at < today_end
    ).count()

    # Order type breakdown
    type_breakdown = db.query(
        Order.order_type,
        func.count(Order.id).label("count")
    ).filter(
        Order.tenant_id == tenant_id
    ).group_by(Order.order_type).all()

    order_type_breakdown = {
        row.order_type: row.count for row in type_breakdown
    }

    # Priority breakdown
    priority_breakdown = db.query(
        Order.priority,
        func.count(Order.id).label("count")
    ).filter(
        Order.tenant_id == tenant_id
    ).group_by(Order.priority).all()

    priority_breakdown_dict = {
        row.priority: row.count for row in priority_breakdown
    }

    # Status breakdown
    status_breakdown = db.query(
        Order.status,
        func.count(Order.id).label("count")
    ).filter(
        Order.tenant_id == tenant_id
    ).group_by(Order.status).all()

    status_breakdown_dict = {
        row.status: row.count for row in status_breakdown
    }

    return OrderStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_today=completed_today,
        order_type_breakdown=order_type_breakdown,
        priority_breakdown=priority_breakdown_dict,
        status_breakdown=status_breakdown_dict
    )


# ==================== Root ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "orders-service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8012))
    uvicorn.run(app, host="0.0.0.0", port=port)
