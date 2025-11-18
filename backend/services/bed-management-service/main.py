"""
Bed Management Service - Hospital Beds and Ward Management
Manages wards, beds, and bed assignments for inpatient care
"""
import os
import sys
from datetime import datetime
from typing import List, Optional
from uuid import UUID

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, case
from loguru import logger

from shared.database.connection import get_db, engine
from shared.database.models import Base, Ward, Bed, BedAssignment, Patient, Admission
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    WardCreate, WardUpdate, WardResponse, WardListResponse, WardWithStats,
    BedCreate, BedUpdate, BedResponse, BedListResponse, BedWithDetails,
    BedAssignmentCreate, BedAssignmentEnd, BedAssignmentResponse,
    BedAssignmentListResponse, BedAssignmentWithDetails,
    BedTransferRequest, BulkBedCreate, BulkBedCreateResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Bed Management Service",
    description="Hospital ward and bed management for IPD",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "bed-management-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Ward Management ====================

@app.post(
    "/api/v1/bed-management/wards",
    response_model=WardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Wards"]
)
async def create_ward(
    ward_data: WardCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new hospital ward

    Creates a ward with specified capacity and type (general, ICU, HDU, etc.)
    """
    try:
        # Check for duplicate code within tenant
        existing = db.query(Ward).filter(
            Ward.tenant_id == ward_data.tenant_id,
            Ward.code == ward_data.code
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ward with code '{ward_data.code}' already exists"
            )

        # Create ward
        ward = Ward(
            tenant_id=ward_data.tenant_id,
            location_id=ward_data.location_id,
            code=ward_data.code,
            name=ward_data.name,
            type=ward_data.type,
            floor=ward_data.floor,
            capacity=ward_data.capacity,
            is_active=True
        )

        db.add(ward)
        db.commit()
        db.refresh(ward)

        logger.info(f"Created ward {ward.id}: {ward.name}")

        # Publish event
        await publish_event(
            event_type=EventType.WARD_CREATED,
            tenant_id=str(ward_data.tenant_id),
            payload={
                "ward_id": str(ward.id),
                "code": ward.code,
                "name": ward.name,
                "type": ward.type,
                "capacity": ward.capacity
            },
            source_service="bed-management-service"
        )

        return ward

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ward: {str(e)}"
        )


@app.get(
    "/api/v1/bed-management/wards",
    response_model=WardListResponse,
    tags=["Wards"]
)
async def list_wards(
    tenant_id: Optional[UUID] = Query(None),
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List wards with optional filters"""
    try:
        query = db.query(Ward)

        if tenant_id:
            query = query.filter(Ward.tenant_id == tenant_id)

        if type:
            query = query.filter(Ward.type == type.lower())

        if is_active is not None:
            query = query.filter(Ward.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        wards = query.order_by(Ward.name).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return WardListResponse(
            total=total,
            wards=wards,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing wards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list wards"
        )


@app.get(
    "/api/v1/bed-management/wards/{ward_id}",
    response_model=WardResponse,
    tags=["Wards"]
)
async def get_ward(
    ward_id: UUID,
    db: Session = Depends(get_db)
):
    """Get ward by ID"""
    try:
        ward = db.query(Ward).filter(Ward.id == ward_id).first()

        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )

        return ward

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ward"
        )


@app.get(
    "/api/v1/bed-management/wards/{ward_id}/stats",
    response_model=WardWithStats,
    tags=["Wards"]
)
async def get_ward_stats(
    ward_id: UUID,
    db: Session = Depends(get_db)
):
    """Get ward with occupancy statistics"""
    try:
        ward = db.query(Ward).filter(Ward.id == ward_id).first()

        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )

        # Get bed statistics
        bed_stats = db.query(
            func.count(Bed.id).label("total"),
            func.sum(case((Bed.status == "occupied", 1), else_=0)).label("occupied"),
            func.sum(case((Bed.status == "available", 1), else_=0)).label("available"),
            func.sum(case((Bed.status == "cleaning", 1), else_=0)).label("cleaning")
        ).filter(Bed.ward_id == ward_id).first()

        total_beds = bed_stats.total or 0
        occupied = bed_stats.occupied or 0
        available = bed_stats.available or 0
        cleaning = bed_stats.cleaning or 0

        occupancy_rate = (occupied / total_beds * 100) if total_beds > 0 else 0.0

        return WardWithStats(
            id=ward.id,
            tenant_id=ward.tenant_id,
            code=ward.code,
            name=ward.name,
            type=ward.type,
            floor=ward.floor,
            capacity=ward.capacity,
            is_active=ward.is_active,
            total_beds=total_beds,
            occupied_beds=occupied,
            available_beds=available,
            cleaning_beds=cleaning,
            occupancy_rate=round(occupancy_rate, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ward stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ward statistics"
        )


@app.patch(
    "/api/v1/bed-management/wards/{ward_id}",
    response_model=WardResponse,
    tags=["Wards"]
)
async def update_ward(
    ward_id: UUID,
    ward_update: WardUpdate,
    db: Session = Depends(get_db)
):
    """Update ward details"""
    try:
        ward = db.query(Ward).filter(Ward.id == ward_id).first()

        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )

        # Update fields
        if ward_update.name:
            ward.name = ward_update.name

        if ward_update.type:
            ward.type = ward_update.type

        if ward_update.floor is not None:
            ward.floor = ward_update.floor

        if ward_update.capacity is not None:
            ward.capacity = ward_update.capacity

        if ward_update.is_active is not None:
            ward.is_active = ward_update.is_active

        ward.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ward)

        logger.info(f"Updated ward {ward_id}")

        return ward

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ward"
        )


# ==================== Bed Management ====================

@app.post(
    "/api/v1/bed-management/wards/{ward_id}/beds",
    response_model=BedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Beds"]
)
async def create_bed(
    ward_id: UUID,
    bed_data: BedCreate,
    db: Session = Depends(get_db)
):
    """Create a bed in a ward"""
    try:
        # Validate ward exists
        ward = db.query(Ward).filter(Ward.id == ward_id).first()

        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )

        # Check for duplicate code within ward
        existing = db.query(Bed).filter(
            Bed.ward_id == ward_id,
            Bed.code == bed_data.code
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bed with code '{bed_data.code}' already exists in this ward"
            )

        # Create bed
        bed = Bed(
            tenant_id=bed_data.tenant_id,
            ward_id=ward_id,
            code=bed_data.code,
            type=bed_data.type,
            status="available"
        )

        db.add(bed)
        db.commit()
        db.refresh(bed)

        logger.info(f"Created bed {bed.id}: {bed.code} in ward {ward.name}")

        # Publish event
        await publish_event(
            event_type=EventType.BED_CREATED,
            tenant_id=str(bed_data.tenant_id),
            payload={
                "bed_id": str(bed.id),
                "ward_id": str(ward_id),
                "code": bed.code,
                "type": bed.type,
                "status": bed.status
            },
            source_service="bed-management-service"
        )

        return bed

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bed: {str(e)}"
        )


@app.post(
    "/api/v1/bed-management/wards/{ward_id}/beds/bulk",
    response_model=BulkBedCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Beds"]
)
async def create_beds_bulk(
    ward_id: UUID,
    bulk_data: BulkBedCreate,
    db: Session = Depends(get_db)
):
    """Create multiple beds at once in a ward"""
    try:
        # Validate ward exists
        ward = db.query(Ward).filter(Ward.id == ward_id).first()

        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )

        created_beds = []
        bed_ids = []
        bed_codes = []

        for i in range(bulk_data.count):
            bed_number = bulk_data.start_number + i
            bed_code = f"{bulk_data.bed_prefix}{bed_number}"

            # Check if bed already exists
            existing = db.query(Bed).filter(
                Bed.ward_id == ward_id,
                Bed.code == bed_code
            ).first()

            if not existing:
                bed = Bed(
                    tenant_id=bulk_data.tenant_id,
                    ward_id=ward_id,
                    code=bed_code,
                    type=bulk_data.bed_type,
                    status="available"
                )
                db.add(bed)
                created_beds.append(bed)

        db.commit()

        # Refresh and collect IDs
        for bed in created_beds:
            db.refresh(bed)
            bed_ids.append(bed.id)
            bed_codes.append(bed.code)

        logger.info(f"Created {len(created_beds)} beds in ward {ward.name}")

        return BulkBedCreateResponse(
            created_count=len(created_beds),
            bed_ids=bed_ids,
            bed_codes=bed_codes
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating beds in bulk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create beds: {str(e)}"
        )


@app.get(
    "/api/v1/bed-management/beds",
    response_model=BedListResponse,
    tags=["Beds"]
)
async def list_beds(
    ward_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List beds with optional filters"""
    try:
        query = db.query(Bed)

        if ward_id:
            query = query.filter(Bed.ward_id == ward_id)

        if status:
            query = query.filter(Bed.status == status.lower())

        if type:
            query = query.filter(Bed.type == type.lower())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        beds = query.order_by(Bed.code).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return BedListResponse(
            total=total,
            beds=beds,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing beds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list beds"
        )


@app.get(
    "/api/v1/bed-management/beds/{bed_id}",
    response_model=BedWithDetails,
    tags=["Beds"]
)
async def get_bed(
    bed_id: UUID,
    db: Session = Depends(get_db)
):
    """Get bed with current assignment details"""
    try:
        bed = db.query(Bed).options(
            joinedload(Bed.ward)
        ).filter(Bed.id == bed_id).first()

        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bed not found"
            )

        # Get current assignment
        current_assignment = db.query(BedAssignment).options(
            joinedload(BedAssignment.patient)
        ).filter(
            BedAssignment.bed_id == bed_id,
            BedAssignment.status == "active"
        ).first()

        patient_name = None
        if current_assignment and current_assignment.patient:
            patient_name = f"{current_assignment.patient.first_name} {current_assignment.patient.last_name}"

        return BedWithDetails(
            id=bed.id,
            tenant_id=bed.tenant_id,
            ward_id=bed.ward_id,
            ward_code=bed.ward.code,
            ward_name=bed.ward.name,
            code=bed.code,
            type=bed.type,
            status=bed.status,
            current_patient_id=current_assignment.patient_id if current_assignment else None,
            current_patient_name=patient_name,
            current_assignment_id=current_assignment.id if current_assignment else None,
            assigned_since=current_assignment.start_time if current_assignment else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bed"
        )


@app.patch(
    "/api/v1/bed-management/beds/{bed_id}",
    response_model=BedResponse,
    tags=["Beds"]
)
async def update_bed(
    bed_id: UUID,
    bed_update: BedUpdate,
    db: Session = Depends(get_db)
):
    """Update bed status or type"""
    try:
        bed = db.query(Bed).filter(Bed.id == bed_id).first()

        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bed not found"
            )

        old_status = bed.status

        # Update fields
        if bed_update.type:
            bed.type = bed_update.type

        if bed_update.status:
            bed.status = bed_update.status

        bed.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(bed)

        logger.info(f"Updated bed {bed_id}: status {old_status} -> {bed.status}")

        # Publish event if status changed
        if bed_update.status and old_status != bed.status:
            await publish_event(
                event_type=EventType.BED_STATUS_CHANGED,
                tenant_id=str(bed.tenant_id),
                payload={
                    "bed_id": str(bed.id),
                    "code": bed.code,
                    "old_status": old_status,
                    "new_status": bed.status
                },
                source_service="bed-management-service"
            )

        return bed

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating bed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bed"
        )


# ==================== Bed Assignments ====================

@app.post(
    "/api/v1/bed-management/bed-assignments",
    response_model=BedAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Bed Assignments"]
)
async def create_bed_assignment(
    assignment_data: BedAssignmentCreate,
    db: Session = Depends(get_db)
):
    """
    Assign a patient to a bed

    Validates bed availability and sets bed status to occupied
    """
    try:
        # Validate bed exists and is available
        bed = db.query(Bed).filter(Bed.id == assignment_data.bed_id).first()

        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bed not found"
            )

        if bed.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bed is not available (current status: {bed.status})"
            )

        # Check if patient already has active bed assignment
        existing_assignment = db.query(BedAssignment).filter(
            BedAssignment.patient_id == assignment_data.patient_id,
            BedAssignment.status == "active"
        ).first()

        if existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Patient already has an active bed assignment (bed: {existing_assignment.bed_id})"
            )

        # Create assignment
        assignment = BedAssignment(
            tenant_id=assignment_data.tenant_id,
            bed_id=assignment_data.bed_id,
            patient_id=assignment_data.patient_id,
            encounter_id=assignment_data.encounter_id,
            admission_id=assignment_data.admission_id,
            start_time=assignment_data.start_time or datetime.utcnow(),
            status="active"
        )

        db.add(assignment)

        # Update bed status
        bed.status = "occupied"
        bed.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assignment)

        logger.info(
            f"Created bed assignment {assignment.id}: "
            f"patient {assignment_data.patient_id} -> bed {bed.code}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.BED_ASSIGNED,
            tenant_id=str(assignment_data.tenant_id),
            payload={
                "bed_assignment_id": str(assignment.id),
                "bed_id": str(assignment_data.bed_id),
                "patient_id": str(assignment_data.patient_id),
                "encounter_id": str(assignment_data.encounter_id),
                "admission_id": str(assignment_data.admission_id) if assignment_data.admission_id else None
            },
            source_service="bed-management-service"
        )

        return assignment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bed assignment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bed assignment: {str(e)}"
        )


@app.post(
    "/api/v1/bed-management/bed-assignments/{assignment_id}/end",
    response_model=BedAssignmentResponse,
    tags=["Bed Assignments"]
)
async def end_bed_assignment(
    assignment_id: UUID,
    end_data: BedAssignmentEnd,
    db: Session = Depends(get_db)
):
    """
    End a bed assignment (for discharge or transfer)

    Releases the bed (sets to cleaning or available)
    """
    try:
        assignment = db.query(BedAssignment).filter(
            BedAssignment.id == assignment_id,
            BedAssignment.status == "active"
        ).first()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active bed assignment not found"
            )

        # End assignment
        assignment.end_time = end_data.end_time or datetime.utcnow()
        assignment.status = end_data.status
        assignment.updated_at = datetime.utcnow()

        # Update bed status (cleaning by default)
        bed = db.query(Bed).filter(Bed.id == assignment.bed_id).first()
        if bed:
            bed.status = "cleaning"
            bed.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assignment)

        logger.info(f"Ended bed assignment {assignment_id}: status={end_data.status}")

        # Publish event
        await publish_event(
            event_type=EventType.BED_RELEASED,
            tenant_id=str(assignment.tenant_id),
            payload={
                "bed_assignment_id": str(assignment.id),
                "bed_id": str(assignment.bed_id),
                "patient_id": str(assignment.patient_id),
                "status": end_data.status,
                "reason": end_data.reason
            },
            source_service="bed-management-service"
        )

        return assignment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error ending bed assignment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end bed assignment"
        )


@app.post(
    "/api/v1/bed-management/admissions/{admission_id}/transfer-bed",
    response_model=dict,
    tags=["Bed Assignments"]
)
async def transfer_patient_bed(
    admission_id: UUID,
    transfer_data: BedTransferRequest,
    db: Session = Depends(get_db)
):
    """
    Transfer patient from one bed to another

    Ends current assignment and creates new one atomically
    """
    try:
        # Validate beds
        from_bed = db.query(Bed).filter(Bed.id == transfer_data.from_bed_id).first()
        to_bed = db.query(Bed).filter(Bed.id == transfer_data.to_bed_id).first()

        if not from_bed or not to_bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both beds not found"
            )

        if to_bed.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target bed is not available (status: {to_bed.status})"
            )

        # Find current assignment
        current_assignment = db.query(BedAssignment).filter(
            BedAssignment.admission_id == admission_id,
            BedAssignment.bed_id == transfer_data.from_bed_id,
            BedAssignment.status == "active"
        ).first()

        if not current_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active bed assignment not found for this admission and bed"
            )

        transfer_time = transfer_data.transfer_time or datetime.utcnow()

        # End current assignment
        current_assignment.end_time = transfer_time
        current_assignment.status = "transferred"
        current_assignment.updated_at = datetime.utcnow()

        # Create new assignment
        new_assignment = BedAssignment(
            tenant_id=current_assignment.tenant_id,
            bed_id=transfer_data.to_bed_id,
            patient_id=current_assignment.patient_id,
            encounter_id=current_assignment.encounter_id,
            admission_id=admission_id,
            start_time=transfer_time,
            status="active"
        )

        db.add(new_assignment)

        # Update bed statuses
        from_bed.status = "cleaning"
        from_bed.updated_at = datetime.utcnow()

        to_bed.status = "occupied"
        to_bed.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(new_assignment)

        logger.info(
            f"Transferred patient {current_assignment.patient_id}: "
            f"bed {from_bed.code} -> {to_bed.code}"
        )

        # Publish event
        await publish_event(
            event_type=EventType.ADMISSION_BED_TRANSFERRED,
            tenant_id=str(current_assignment.tenant_id),
            payload={
                "admission_id": str(admission_id),
                "patient_id": str(current_assignment.patient_id),
                "from_bed_id": str(transfer_data.from_bed_id),
                "from_bed_code": from_bed.code,
                "to_bed_id": str(transfer_data.to_bed_id),
                "to_bed_code": to_bed.code,
                "old_assignment_id": str(current_assignment.id),
                "new_assignment_id": str(new_assignment.id),
                "reason": transfer_data.reason
            },
            source_service="bed-management-service"
        )

        return {
            "old_bed_assignment_id": str(current_assignment.id),
            "new_bed_assignment_id": str(new_assignment.id),
            "from_bed_code": from_bed.code,
            "to_bed_code": to_bed.code,
            "transfer_time": transfer_time.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error transferring bed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transfer bed"
        )


@app.get(
    "/api/v1/bed-management/bed-assignments",
    response_model=BedAssignmentListResponse,
    tags=["Bed Assignments"]
)
async def list_bed_assignments(
    bed_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    admission_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List bed assignments with filters"""
    try:
        query = db.query(BedAssignment)

        if bed_id:
            query = query.filter(BedAssignment.bed_id == bed_id)

        if patient_id:
            query = query.filter(BedAssignment.patient_id == patient_id)

        if admission_id:
            query = query.filter(BedAssignment.admission_id == admission_id)

        if status:
            query = query.filter(BedAssignment.status == status.lower())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        assignments = query.order_by(
            BedAssignment.start_time.desc()
        ).offset(offset).limit(page_size).all()

        has_next = (offset + page_size) < total
        has_previous = page > 1

        return BedAssignmentListResponse(
            total=total,
            assignments=assignments,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        logger.error(f"Error listing bed assignments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list bed assignments"
        )


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Bed Management Service starting up...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info("Bed Management Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009, reload=True)
