"""
Tariff Pricebook Service - Port 8058
Manages service items, tariff groups, pricing rates, and package definitions
Maps to FHIR ChargeItemDefinition and PlanDefinition
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    ServiceItem, TariffGroup, TariffRate, PackageDefinition, PackageInclusion
)
from schemas import (
    ServiceItemResponse, TariffGroupResponse, TariffRateResponse,
    PackageDefinitionResponse, PackageInclusionResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Tariff Pricebook Service", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Service Item Endpoints
@app.get("/api/v1/tariffs/service-items", response_model=List[ServiceItemResponse], tags=["Service Items"])
async def list_service_items(
    tenant_id: UUID = Query(...),
    category: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List service items (procedures, beds, consultations, labs, imaging, consumables, packages)"""
    query = db.query(ServiceItem).filter(ServiceItem.tenant_id == tenant_id)

    if category:
        query = query.filter(ServiceItem.category == category)

    if search_text:
        query = query.filter(
            or_(
                ServiceItem.name.ilike(f"%{search_text}%"),
                ServiceItem.code.ilike(f"%{search_text}%")
            )
        )

    if active_only:
        query = query.filter(ServiceItem.is_active == True)

    return query.order_by(ServiceItem.name).all()


@app.get("/api/v1/tariffs/service-items/{item_id}", response_model=ServiceItemResponse, tags=["Service Items"])
async def get_service_item(item_id: UUID, db: Session = Depends(get_db)):
    """Get service item details"""
    item = db.query(ServiceItem).filter(ServiceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Service item not found")
    return item


# Tariff Group Endpoints
@app.get("/api/v1/tariffs/tariff-groups", response_model=List[TariffGroupResponse], tags=["Tariff Groups"])
async def list_tariff_groups(
    tenant_id: UUID = Query(...),
    payer_plan_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List tariff groups (pricing categories)"""
    query = db.query(TariffGroup).filter(TariffGroup.tenant_id == tenant_id)

    if payer_plan_id:
        query = query.filter(TariffGroup.payer_plan_id == payer_plan_id)

    return query.order_by(TariffGroup.name).all()


@app.get("/api/v1/tariffs/tariff-groups/{group_id}", response_model=TariffGroupResponse, tags=["Tariff Groups"])
async def get_tariff_group(group_id: UUID, db: Session = Depends(get_db)):
    """Get tariff group details"""
    group = db.query(TariffGroup).filter(TariffGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Tariff group not found")
    return group


# Tariff Rate Endpoints
@app.get("/api/v1/tariffs/rates", response_model=List[TariffRateResponse], tags=["Tariff Rates"])
async def list_tariff_rates(
    tariff_group_id: Optional[UUID] = Query(None),
    service_item_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List tariff rates with optional filters"""
    query = db.query(TariffRate)

    if tariff_group_id:
        query = query.filter(TariffRate.tariff_group_id == tariff_group_id)

    if service_item_id:
        query = query.filter(TariffRate.service_item_id == service_item_id)

    if active_only:
        # Filter for rates that are currently active (within effective dates)
        today = datetime.now().date()
        query = query.filter(
            or_(
                TariffRate.effective_from == None,
                TariffRate.effective_from <= today
            ),
            or_(
                TariffRate.effective_to == None,
                TariffRate.effective_to >= today
            )
        )

    return query.all()


# Package Definition Endpoints
@app.get("/api/v1/tariffs/packages", response_model=List[PackageDefinitionResponse], tags=["Packages"])
async def list_packages(
    tenant_id: UUID = Query(...),
    procedure_id: Optional[UUID] = Query(None, description="procedure_catalog_id"),
    payer_plan_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List package definitions"""
    query = db.query(PackageDefinition).filter(PackageDefinition.tenant_id == tenant_id)

    if procedure_id:
        query = query.filter(PackageDefinition.procedure_catalog_id == procedure_id)

    if payer_plan_id:
        query = query.filter(PackageDefinition.payer_plan_id == payer_plan_id)

    if active_only:
        query = query.filter(PackageDefinition.is_active == True)

    return query.order_by(PackageDefinition.name).all()


@app.get("/api/v1/tariffs/packages/{package_id}", response_model=PackageDefinitionResponse, tags=["Packages"])
async def get_package(package_id: UUID, db: Session = Depends(get_db)):
    """Get package definition details"""
    package = db.query(PackageDefinition).filter(PackageDefinition.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@app.get("/api/v1/tariffs/packages/{package_id}/inclusions", response_model=List[PackageInclusionResponse], tags=["Packages"])
async def list_package_inclusions(package_id: UUID, db: Session = Depends(get_db)):
    """List what's included in a package"""
    # Verify package exists
    package = db.query(PackageDefinition).filter(PackageDefinition.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return db.query(PackageInclusion).filter(
        PackageInclusion.package_definition_id == package_id
    ).all()


@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "tariff-pricebook-service", "status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8058)
