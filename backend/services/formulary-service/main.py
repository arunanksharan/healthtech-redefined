"""
Formulary Service - Port 8043
Hospital/tenant-specific formulary, restrictions, substitution rules
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, joinedload

from shared.database.models import (
    FormularyEntry, FormularyRestriction, FormularySubstitutionRule,
    MedicationProduct, MedicationMolecule, MedicationRoute, Tenant
)
from schemas import (
    FormularyEntryCreate, FormularyEntryResponse,
    FormularyRestrictionCreate, FormularyRestrictionResponse,
    FormularySubstitutionRuleCreate, FormularySubstitutionRuleResponse,
    FormularyAlternativeResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Formulary Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Formulary Entry Endpoints
@app.post("/api/v1/formulary/entries", response_model=FormularyEntryResponse, status_code=201, tags=["Formulary Entries"])
async def create_formulary_entry(
    entry_data: FormularyEntryCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add a medication product to formulary"""
    # Check if entry already exists
    existing = db.query(FormularyEntry).filter(
        FormularyEntry.tenant_id == entry_data.tenant_id,
        FormularyEntry.medication_product_id == entry_data.medication_product_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Formulary entry already exists for this product")

    # Verify product exists
    product = db.query(MedicationProduct).filter(MedicationProduct.id == entry_data.medication_product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Medication product not found")

    # Verify route if provided
    if entry_data.default_route_id:
        route = db.query(MedicationRoute).filter(MedicationRoute.id == entry_data.default_route_id).first()
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

    formulary_entry = FormularyEntry(
        tenant_id=entry_data.tenant_id,
        medication_product_id=entry_data.medication_product_id,
        is_formulary=entry_data.is_formulary,
        restriction_level=entry_data.restriction_level,
        default_route_id=entry_data.default_route_id,
        default_frequency=entry_data.default_frequency,
        notes=entry_data.notes
    )
    db.add(formulary_entry)
    db.commit()
    db.refresh(formulary_entry)

    logger.info(f"Formulary entry created for product: {entry_data.medication_product_id}")
    return formulary_entry

@app.get("/api/v1/formulary/entries", response_model=List[FormularyEntryResponse], tags=["Formulary Entries"])
async def list_formulary_entries(
    tenant_id: UUID = Query(...),
    is_formulary: Optional[bool] = Query(None),
    restriction_level: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List formulary entries for a tenant"""
    query = db.query(FormularyEntry).filter(FormularyEntry.tenant_id == tenant_id)

    if is_formulary is not None:
        query = query.filter(FormularyEntry.is_formulary == is_formulary)
    if restriction_level:
        query = query.filter(FormularyEntry.restriction_level == restriction_level)
    if search_text:
        query = query.join(MedicationProduct).join(MedicationMolecule).filter(
            (MedicationProduct.brand_name.ilike(f"%{search_text}%")) |
            (MedicationMolecule.name.ilike(f"%{search_text}%"))
        )

    return query.order_by(FormularyEntry.created_at.desc()).all()

@app.get("/api/v1/formulary/entries/{entry_id}", response_model=FormularyEntryResponse, tags=["Formulary Entries"])
async def get_formulary_entry(entry_id: UUID, db: Session = Depends(get_db)):
    """Get formulary entry details"""
    entry = db.query(FormularyEntry).filter(FormularyEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Formulary entry not found")
    return entry

@app.patch("/api/v1/formulary/entries/{entry_id}", response_model=FormularyEntryResponse, tags=["Formulary Entries"])
async def update_formulary_entry(
    entry_id: UUID,
    restriction_level: Optional[str] = None,
    is_formulary: Optional[bool] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update formulary entry"""
    entry = db.query(FormularyEntry).filter(FormularyEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Formulary entry not found")

    if restriction_level is not None:
        entry.restriction_level = restriction_level
    if is_formulary is not None:
        entry.is_formulary = is_formulary
    if notes is not None:
        entry.notes = notes

    db.commit()
    db.refresh(entry)

    logger.info(f"Formulary entry updated: {entry_id}")
    return entry

# Formulary Restriction Endpoints
@app.post("/api/v1/formulary/restrictions", response_model=FormularyRestrictionResponse, status_code=201, tags=["Restrictions"])
async def create_formulary_restriction(
    restriction_data: FormularyRestrictionCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add restriction to formulary entry"""
    # Verify entry exists
    entry = db.query(FormularyEntry).filter(FormularyEntry.id == restriction_data.formulary_entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Formulary entry not found")

    restriction = FormularyRestriction(
        formulary_entry_id=restriction_data.formulary_entry_id,
        restriction_type=restriction_data.restriction_type,
        allowed_specialties=restriction_data.allowed_specialties,
        indication_regex=restriction_data.indication_regex,
        approval_required=restriction_data.approval_required,
        approval_role=restriction_data.approval_role
    )
    db.add(restriction)
    db.commit()
    db.refresh(restriction)

    logger.info(f"Formulary restriction created for entry: {restriction_data.formulary_entry_id}")
    return restriction

@app.get("/api/v1/formulary/restrictions", response_model=List[FormularyRestrictionResponse], tags=["Restrictions"])
async def list_restrictions(
    formulary_entry_id: Optional[UUID] = Query(None),
    restriction_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List formulary restrictions"""
    query = db.query(FormularyRestriction)

    if formulary_entry_id:
        query = query.filter(FormularyRestriction.formulary_entry_id == formulary_entry_id)
    if restriction_type:
        query = query.filter(FormularyRestriction.restriction_type == restriction_type)

    return query.all()

# Formulary Substitution Rule Endpoints
@app.post("/api/v1/formulary/substitution-rules", response_model=FormularySubstitutionRuleResponse, status_code=201, tags=["Substitution Rules"])
async def create_substitution_rule(
    rule_data: FormularySubstitutionRuleCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a substitution rule"""
    # Verify molecules exist
    from_molecule = db.query(MedicationMolecule).filter(MedicationMolecule.id == rule_data.from_molecule_id).first()
    if not from_molecule:
        raise HTTPException(status_code=404, detail="From molecule not found")

    to_molecule = db.query(MedicationMolecule).filter(MedicationMolecule.id == rule_data.to_molecule_id).first()
    if not to_molecule:
        raise HTTPException(status_code=404, detail="To molecule not found")

    substitution_rule = FormularySubstitutionRule(
        tenant_id=rule_data.tenant_id,
        from_molecule_id=rule_data.from_molecule_id,
        to_molecule_id=rule_data.to_molecule_id,
        rule_type=rule_data.rule_type,
        conditions=rule_data.conditions
    )
    db.add(substitution_rule)
    db.commit()
    db.refresh(substitution_rule)

    logger.info(f"Substitution rule created: {from_molecule.name} -> {to_molecule.name}")
    return substitution_rule

@app.get("/api/v1/formulary/substitution-rules", response_model=List[FormularySubstitutionRuleResponse], tags=["Substitution Rules"])
async def list_substitution_rules(
    tenant_id: UUID = Query(...),
    from_molecule_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List substitution rules"""
    query = db.query(FormularySubstitutionRule).filter(
        FormularySubstitutionRule.tenant_id == tenant_id
    )

    if from_molecule_id:
        query = query.filter(FormularySubstitutionRule.from_molecule_id == from_molecule_id)

    return query.all()

# Alternatives Endpoint
@app.get("/api/v1/formulary/alternatives", response_model=List[FormularyAlternativeResponse], tags=["Alternatives"])
async def get_alternatives(
    tenant_id: UUID = Query(...),
    product_id: Optional[UUID] = Query(None),
    molecule_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get formulary alternatives for a product or molecule
    Returns formulary products that could substitute
    """
    alternatives = []

    # Get molecule ID if product is provided
    if product_id and not molecule_id:
        product = db.query(MedicationProduct).filter(MedicationProduct.id == product_id).first()
        if product:
            molecule_id = product.molecule_id

    if not molecule_id:
        raise HTTPException(status_code=400, detail="Either product_id or molecule_id must be provided")

    # Find all products with same molecule that are in formulary
    formulary_entries = db.query(FormularyEntry).options(
        joinedload(FormularyEntry.medication_product).joinedload(MedicationProduct.molecule),
        joinedload(FormularyEntry.medication_product).joinedload(MedicationProduct.route)
    ).join(MedicationProduct).filter(
        FormularyEntry.tenant_id == tenant_id,
        MedicationProduct.molecule_id == molecule_id,
        FormularyEntry.is_formulary == True
    ).all()

    for entry in formulary_entries:
        product = entry.medication_product
        alternatives.append({
            "product_id": product.id,
            "brand_name": product.brand_name,
            "molecule_name": product.molecule.name,
            "strength": product.strength,
            "route_code": product.route.code if product.route else None,
            "is_formulary": entry.is_formulary,
            "restriction_level": entry.restriction_level,
            "substitution_rule_type": None
        })

    # Also check for therapeutic substitution rules
    substitution_rules = db.query(FormularySubstitutionRule).filter(
        FormularySubstitutionRule.tenant_id == tenant_id,
        FormularySubstitutionRule.from_molecule_id == molecule_id
    ).all()

    for rule in substitution_rules:
        # Find formulary products for the substitute molecule
        substitute_entries = db.query(FormularyEntry).options(
            joinedload(FormularyEntry.medication_product).joinedload(MedicationProduct.molecule),
            joinedload(FormularyEntry.medication_product).joinedload(MedicationProduct.route)
        ).join(MedicationProduct).filter(
            FormularyEntry.tenant_id == tenant_id,
            MedicationProduct.molecule_id == rule.to_molecule_id,
            FormularyEntry.is_formulary == True
        ).all()

        for entry in substitute_entries:
            product = entry.medication_product
            alternatives.append({
                "product_id": product.id,
                "brand_name": product.brand_name,
                "molecule_name": product.molecule.name,
                "strength": product.strength,
                "route_code": product.route.code if product.route else None,
                "is_formulary": entry.is_formulary,
                "restriction_level": entry.restriction_level,
                "substitution_rule_type": rule.rule_type
            })

    return alternatives

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "formulary-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8043)
