"""
Medication Catalog Service - Port 8042
Core medication master: APIs for drug molecules, forms, strengths, routes
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker, joinedload

from shared.database.models import (
    MedicationMolecule, MedicationRoute, MedicationDoseForm,
    MedicationProduct, Tenant
)
from schemas import (
    MedicationMoleculeCreate, MedicationMoleculeResponse,
    MedicationRouteCreate, MedicationRouteResponse,
    MedicationDoseFormCreate, MedicationDoseFormResponse,
    MedicationProductCreate, MedicationProductResponse,
    MedicationProductDetailResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Medication Catalog Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Medication Molecule Endpoints
@app.post("/api/v1/medications/catalog/molecules", response_model=MedicationMoleculeResponse, status_code=201, tags=["Molecules"])
async def create_molecule(
    molecule_data: MedicationMoleculeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a medication molecule (generic drug)"""
    existing = db.query(MedicationMolecule).filter(
        MedicationMolecule.name == molecule_data.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Molecule with this name already exists")

    molecule = MedicationMolecule(
        tenant_id=molecule_data.tenant_id,
        global_code=molecule_data.global_code,
        name=molecule_data.name,
        synonyms=molecule_data.synonyms,
        atc_code=molecule_data.atc_code,
        drug_class=molecule_data.drug_class,
        is_controlled_substance=molecule_data.is_controlled_substance,
        is_high_alert=molecule_data.is_high_alert
    )
    db.add(molecule)
    db.commit()
    db.refresh(molecule)

    logger.info(f"Medication molecule created: {molecule.name}")
    return molecule

@app.get("/api/v1/medications/catalog/molecules", response_model=List[MedicationMoleculeResponse], tags=["Molecules"])
async def list_molecules(
    search_text: Optional[str] = Query(None),
    drug_class: Optional[str] = Query(None),
    is_controlled_substance: Optional[bool] = Query(None),
    is_high_alert: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Search and list medication molecules"""
    query = db.query(MedicationMolecule)

    if search_text:
        query = query.filter(
            or_(
                MedicationMolecule.name.ilike(f"%{search_text}%"),
                MedicationMolecule.global_code.ilike(f"%{search_text}%"),
                MedicationMolecule.atc_code.ilike(f"%{search_text}%")
            )
        )
    if drug_class:
        query = query.filter(MedicationMolecule.drug_class == drug_class)
    if is_controlled_substance is not None:
        query = query.filter(MedicationMolecule.is_controlled_substance == is_controlled_substance)
    if is_high_alert is not None:
        query = query.filter(MedicationMolecule.is_high_alert == is_high_alert)

    return query.order_by(MedicationMolecule.name).all()

@app.get("/api/v1/medications/catalog/molecules/{molecule_id}", response_model=MedicationMoleculeResponse, tags=["Molecules"])
async def get_molecule(molecule_id: UUID, db: Session = Depends(get_db)):
    """Get molecule details"""
    molecule = db.query(MedicationMolecule).filter(MedicationMolecule.id == molecule_id).first()
    if not molecule:
        raise HTTPException(status_code=404, detail="Molecule not found")
    return molecule

# Medication Route Endpoints
@app.post("/api/v1/medications/catalog/routes", response_model=MedicationRouteResponse, status_code=201, tags=["Routes"])
async def create_route(
    route_data: MedicationRouteCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a medication route"""
    existing = db.query(MedicationRoute).filter(MedicationRoute.code == route_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Route code already exists")

    route = MedicationRoute(
        code=route_data.code,
        name=route_data.name,
        description=route_data.description
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    logger.info(f"Medication route created: {route.code}")
    return route

@app.get("/api/v1/medications/catalog/routes", response_model=List[MedicationRouteResponse], tags=["Routes"])
async def list_routes(db: Session = Depends(get_db)):
    """List all medication routes"""
    return db.query(MedicationRoute).order_by(MedicationRoute.code).all()

@app.get("/api/v1/medications/catalog/routes/{route_id}", response_model=MedicationRouteResponse, tags=["Routes"])
async def get_route(route_id: UUID, db: Session = Depends(get_db)):
    """Get route details"""
    route = db.query(MedicationRoute).filter(MedicationRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

# Medication Dose Form Endpoints
@app.post("/api/v1/medications/catalog/dose-forms", response_model=MedicationDoseFormResponse, status_code=201, tags=["Dose Forms"])
async def create_dose_form(
    form_data: MedicationDoseFormCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a medication dose form"""
    existing = db.query(MedicationDoseForm).filter(MedicationDoseForm.code == form_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dose form code already exists")

    dose_form = MedicationDoseForm(
        code=form_data.code,
        name=form_data.name,
        description=form_data.description
    )
    db.add(dose_form)
    db.commit()
    db.refresh(dose_form)

    logger.info(f"Medication dose form created: {dose_form.code}")
    return dose_form

@app.get("/api/v1/medications/catalog/dose-forms", response_model=List[MedicationDoseFormResponse], tags=["Dose Forms"])
async def list_dose_forms(db: Session = Depends(get_db)):
    """List all medication dose forms"""
    return db.query(MedicationDoseForm).order_by(MedicationDoseForm.code).all()

@app.get("/api/v1/medications/catalog/dose-forms/{form_id}", response_model=MedicationDoseFormResponse, tags=["Dose Forms"])
async def get_dose_form(form_id: UUID, db: Session = Depends(get_db)):
    """Get dose form details"""
    dose_form = db.query(MedicationDoseForm).filter(MedicationDoseForm.id == form_id).first()
    if not dose_form:
        raise HTTPException(status_code=404, detail="Dose form not found")
    return dose_form

# Medication Product Endpoints
@app.post("/api/v1/medications/catalog/products", response_model=MedicationProductResponse, status_code=201, tags=["Products"])
async def create_product(
    product_data: MedicationProductCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a medication product"""
    # Verify molecule exists
    molecule = db.query(MedicationMolecule).filter(MedicationMolecule.id == product_data.molecule_id).first()
    if not molecule:
        raise HTTPException(status_code=404, detail="Molecule not found")

    # Verify dose form if provided
    if product_data.dose_form_id:
        dose_form = db.query(MedicationDoseForm).filter(MedicationDoseForm.id == product_data.dose_form_id).first()
        if not dose_form:
            raise HTTPException(status_code=404, detail="Dose form not found")

    # Verify route if provided
    if product_data.route_id:
        route = db.query(MedicationRoute).filter(MedicationRoute.id == product_data.route_id).first()
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

    product = MedicationProduct(
        tenant_id=product_data.tenant_id,
        molecule_id=product_data.molecule_id,
        brand_name=product_data.brand_name,
        strength=product_data.strength,
        strength_numeric=product_data.strength_numeric,
        strength_unit=product_data.strength_unit,
        dose_form_id=product_data.dose_form_id,
        route_id=product_data.route_id,
        pack_size=product_data.pack_size,
        pack_unit=product_data.pack_unit,
        is_generic=product_data.is_generic,
        is_active=product_data.is_active
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    logger.info(f"Medication product created: {product.brand_name or molecule.name}")
    return product

@app.get("/api/v1/medications/catalog/products", response_model=List[MedicationProductDetailResponse], tags=["Products"])
async def list_products(
    search_text: Optional[str] = Query(None),
    molecule_id: Optional[UUID] = Query(None),
    route: Optional[str] = Query(None),
    form: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db)
):
    """Search and list medication products"""
    query = db.query(MedicationProduct).options(
        joinedload(MedicationProduct.molecule),
        joinedload(MedicationProduct.dose_form),
        joinedload(MedicationProduct.route)
    )

    if search_text:
        query = query.join(MedicationMolecule).filter(
            or_(
                MedicationProduct.brand_name.ilike(f"%{search_text}%"),
                MedicationMolecule.name.ilike(f"%{search_text}%")
            )
        )
    if molecule_id:
        query = query.filter(MedicationProduct.molecule_id == molecule_id)
    if route:
        query = query.join(MedicationRoute).filter(MedicationRoute.code == route)
    if form:
        query = query.join(MedicationDoseForm).filter(MedicationDoseForm.code == form)
    if is_active is not None:
        query = query.filter(MedicationProduct.is_active == is_active)

    return query.order_by(MedicationProduct.brand_name).all()

@app.get("/api/v1/medications/catalog/products/{product_id}", response_model=MedicationProductDetailResponse, tags=["Products"])
async def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get product details with related entities"""
    product = db.query(MedicationProduct).options(
        joinedload(MedicationProduct.molecule),
        joinedload(MedicationProduct.dose_form),
        joinedload(MedicationProduct.route)
    ).filter(MedicationProduct.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "medication-catalog-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8042)
