"""
Lab Catalog Service - Port 8036
Manages master lab test catalog: specimen types, tests, and panels
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    LabSpecimenType, LabTest, LabTestPanel, LabTestPanelItem, Tenant
)
from schemas import (
    LabSpecimenTypeCreate, LabSpecimenTypeResponse,
    LabTestCreate, LabTestResponse,
    LabTestPanelCreate, LabTestPanelResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Lab Catalog Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Specimen Type Endpoints
@app.post("/api/v1/lab-catalog/specimen-types", response_model=LabSpecimenTypeResponse, status_code=201, tags=["Specimen Types"])
async def create_specimen_type(
    specimen_type_data: LabSpecimenTypeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a lab specimen type"""
    existing = db.query(LabSpecimenType).filter(
        LabSpecimenType.code == specimen_type_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Specimen type code already exists")

    specimen_type = LabSpecimenType(
        tenant_id=specimen_type_data.tenant_id,
        code=specimen_type_data.code,
        name=specimen_type_data.name,
        description=specimen_type_data.description,
        container_type=specimen_type_data.container_type,
        handling_instructions=specimen_type_data.handling_instructions,
        storage_temperature_range=specimen_type_data.storage_temperature_range,
        stability_hours=specimen_type_data.stability_hours
    )
    db.add(specimen_type)
    db.commit()
    db.refresh(specimen_type)

    logger.info(f"Lab specimen type created: {specimen_type.code}")
    return specimen_type

@app.get("/api/v1/lab-catalog/specimen-types", response_model=List[LabSpecimenTypeResponse], tags=["Specimen Types"])
async def list_specimen_types(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all lab specimen types"""
    query = db.query(LabSpecimenType)
    if is_active is not None:
        query = query.filter(LabSpecimenType.is_active == is_active)
    return query.all()

@app.get("/api/v1/lab-catalog/specimen-types/{id}", response_model=LabSpecimenTypeResponse, tags=["Specimen Types"])
async def get_specimen_type(id: UUID, db: Session = Depends(get_db)):
    """Get specimen type details"""
    specimen_type = db.query(LabSpecimenType).filter(LabSpecimenType.id == id).first()
    if not specimen_type:
        raise HTTPException(status_code=404, detail="Specimen type not found")
    return specimen_type

# Lab Test Endpoints
@app.post("/api/v1/lab-catalog/tests", response_model=LabTestResponse, status_code=201, tags=["Lab Tests"])
async def create_lab_test(
    test_data: LabTestCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a lab test"""
    existing = db.query(LabTest).filter(LabTest.code == test_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lab test code already exists")

    lab_test = LabTest(
        tenant_id=test_data.tenant_id,
        code=test_data.code,
        name=test_data.name,
        description=test_data.description,
        loinc_code=test_data.loinc_code,
        category=test_data.category,
        default_specimen_type_id=test_data.default_specimen_type_id,
        unit=test_data.unit,
        reference_range=test_data.reference_range,
        critical_range=test_data.critical_range,
        is_panel=test_data.is_panel,
        result_type=test_data.result_type,
        result_value_set=test_data.result_value_set
    )
    db.add(lab_test)
    db.commit()
    db.refresh(lab_test)

    logger.info(f"Lab test created: {lab_test.code}")
    return lab_test

@app.get("/api/v1/lab-catalog/tests", response_model=List[LabTestResponse], tags=["Lab Tests"])
async def list_lab_tests(
    category: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all lab tests with optional filters"""
    query = db.query(LabTest)
    if category:
        query = query.filter(LabTest.category == category)
    if search_text:
        query = query.filter(
            LabTest.name.ilike(f"%{search_text}%") |
            LabTest.code.ilike(f"%{search_text}%")
        )
    if is_active is not None:
        query = query.filter(LabTest.is_active == is_active)
    return query.all()

@app.get("/api/v1/lab-catalog/tests/{id}", response_model=LabTestResponse, tags=["Lab Tests"])
async def get_lab_test(id: UUID, db: Session = Depends(get_db)):
    """Get lab test details"""
    lab_test = db.query(LabTest).filter(LabTest.id == id).first()
    if not lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    return lab_test

# Lab Test Panel Endpoints
@app.post("/api/v1/lab-catalog/panels", response_model=LabTestPanelResponse, status_code=201, tags=["Lab Panels"])
async def create_lab_test_panel(
    panel_data: LabTestPanelCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a lab test panel"""
    # Verify lab test exists
    lab_test = db.query(LabTest).filter(LabTest.id == panel_data.lab_test_id).first()
    if not lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")

    existing = db.query(LabTestPanel).filter(
        LabTestPanel.panel_code == panel_data.panel_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Panel code already exists")

    panel = LabTestPanel(
        lab_test_id=panel_data.lab_test_id,
        panel_code=panel_data.panel_code,
        name=panel_data.name,
        description=panel_data.description
    )
    db.add(panel)
    db.commit()
    db.refresh(panel)

    logger.info(f"Lab test panel created: {panel.panel_code}")
    return panel

@app.get("/api/v1/lab-catalog/panels", response_model=List[LabTestPanelResponse], tags=["Lab Panels"])
async def list_lab_test_panels(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all lab test panels"""
    query = db.query(LabTestPanel)
    if is_active is not None:
        query = query.filter(LabTestPanel.is_active == is_active)
    return query.all()

@app.get("/api/v1/lab-catalog/panels/{id}", response_model=LabTestPanelResponse, tags=["Lab Panels"])
async def get_lab_test_panel(id: UUID, db: Session = Depends(get_db)):
    """Get lab test panel details"""
    panel = db.query(LabTestPanel).filter(LabTestPanel.id == id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Lab test panel not found")
    return panel

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "lab-catalog-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8036)
