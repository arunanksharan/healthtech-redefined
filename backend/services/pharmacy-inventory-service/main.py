"""
Pharmacy Inventory Service - Port 8048
Stock levels, batches, expiry, purchase orders, vendor relationships
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker, joinedload

from shared.database.models import (
    InventoryLocation, InventoryBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderLine,
    MedicationProduct, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    InventoryLocationCreate, InventoryLocationResponse,
    InventoryBatchCreate, InventoryBatchResponse,
    InventoryTransactionCreate, InventoryTransactionResponse,
    VendorCreate, VendorResponse,
    PurchaseOrderCreate, PurchaseOrderResponse,
    PurchaseOrderLineCreate, PurchaseOrderLineResponse,
    StockLevelResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Pharmacy Inventory Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inventory Location Endpoints
@app.post("/api/v1/pharmacy/inventory/locations", response_model=InventoryLocationResponse, status_code=201, tags=["Inventory Locations"])
async def create_location(
    location_data: InventoryLocationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create an inventory location (pharmacy store, ward cupboard)"""
    # Check for duplicate code
    existing = db.query(InventoryLocation).filter(
        InventoryLocation.tenant_id == location_data.tenant_id,
        InventoryLocation.code == location_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Location code already exists for this tenant")

    location = InventoryLocation(
        tenant_id=location_data.tenant_id,
        code=location_data.code,
        name=location_data.name,
        type=location_data.type,
        is_active=location_data.is_active
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    logger.info(f"Inventory location created: {location.code}")
    return location

@app.get("/api/v1/pharmacy/inventory/locations", response_model=List[InventoryLocationResponse], tags=["Inventory Locations"])
async def list_locations(
    tenant_id: UUID = Query(...),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List inventory locations"""
    query = db.query(InventoryLocation).filter(InventoryLocation.tenant_id == tenant_id)

    if is_active is not None:
        query = query.filter(InventoryLocation.is_active == is_active)

    return query.order_by(InventoryLocation.name).all()

# Inventory Batch Endpoints
@app.post("/api/v1/pharmacy/inventory/batches", response_model=InventoryBatchResponse, status_code=201, tags=["Inventory Batches"])
async def create_batch(
    batch_data: InventoryBatchCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create an inventory batch"""
    # Verify product exists
    product = db.query(MedicationProduct).filter(MedicationProduct.id == batch_data.medication_product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Medication product not found")

    # Verify location exists
    location = db.query(InventoryLocation).filter(InventoryLocation.id == batch_data.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    batch = InventoryBatch(
        tenant_id=batch_data.tenant_id,
        medication_product_id=batch_data.medication_product_id,
        batch_number=batch_data.batch_number,
        expiry_date=batch_data.expiry_date,
        current_quantity=batch_data.current_quantity,
        quantity_unit=batch_data.quantity_unit,
        location_id=batch_data.location_id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    logger.info(f"Inventory batch created: {batch.batch_number} for product {batch_data.medication_product_id}")
    return batch

@app.get("/api/v1/pharmacy/inventory/batches", response_model=List[InventoryBatchResponse], tags=["Inventory Batches"])
async def list_batches(
    product_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    expiring_before: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """List inventory batches with filters"""
    query = db.query(InventoryBatch)

    if product_id:
        query = query.filter(InventoryBatch.medication_product_id == product_id)
    if location_id:
        query = query.filter(InventoryBatch.location_id == location_id)
    if expiring_before:
        query = query.filter(InventoryBatch.expiry_date <= expiring_before)

    return query.order_by(InventoryBatch.expiry_date).all()

@app.get("/api/v1/pharmacy/inventory/batches/{batch_id}", response_model=InventoryBatchResponse, tags=["Inventory Batches"])
async def get_batch(batch_id: UUID, db: Session = Depends(get_db)):
    """Get batch details"""
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

# Inventory Transaction Endpoints
@app.post("/api/v1/pharmacy/inventory/transactions", response_model=InventoryTransactionResponse, status_code=201, tags=["Inventory Transactions"])
async def create_transaction(
    transaction_data: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Create an inventory transaction (receive, dispense, adjustment, etc.)
    Automatically updates batch quantity
    """
    # Verify batch exists
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == transaction_data.inventory_batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Update batch quantity
    batch.current_quantity += transaction_data.quantity_delta

    if batch.current_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient inventory quantity")

    transaction = InventoryTransaction(
        tenant_id=batch.tenant_id,
        inventory_batch_id=transaction_data.inventory_batch_id,
        transaction_type=transaction_data.transaction_type,
        quantity_delta=transaction_data.quantity_delta,
        reason=transaction_data.reason,
        related_dispensation_id=transaction_data.related_dispensation_id,
        related_purchase_order_line_id=transaction_data.related_purchase_order_line_id,
        created_by_user_id=current_user_id
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    await publish_event(EventType.INVENTORY_TRANSACTION_CREATED, {
        "transaction_id": str(transaction.id),
        "batch_id": str(batch.id),
        "transaction_type": transaction.transaction_type,
        "quantity_delta": float(transaction.quantity_delta),
        "new_quantity": float(batch.current_quantity)
    })

    logger.info(f"Inventory transaction created: {transaction.transaction_type} - {transaction.quantity_delta}")
    return transaction

@app.get("/api/v1/pharmacy/inventory/transactions", response_model=List[InventoryTransactionResponse], tags=["Inventory Transactions"])
async def list_transactions(
    batch_id: Optional[UUID] = Query(None),
    transaction_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List inventory transactions"""
    query = db.query(InventoryTransaction)

    if batch_id:
        query = query.filter(InventoryTransaction.inventory_batch_id == batch_id)
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)

    return query.order_by(InventoryTransaction.created_at.desc()).all()

# Stock Level Endpoint
@app.get("/api/v1/pharmacy/inventory/stock-levels", response_model=List[StockLevelResponse], tags=["Stock Levels"])
async def get_stock_levels(
    tenant_id: UUID = Query(...),
    location_id: Optional[UUID] = Query(None),
    product_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get current stock levels aggregated by location and product
    """
    query = db.query(
        InventoryBatch.location_id,
        InventoryBatch.medication_product_id,
        func.sum(InventoryBatch.current_quantity).label('total_quantity')
    ).filter(
        InventoryBatch.tenant_id == tenant_id
    ).group_by(
        InventoryBatch.location_id,
        InventoryBatch.medication_product_id
    )

    if location_id:
        query = query.filter(InventoryBatch.location_id == location_id)
    if product_id:
        query = query.filter(InventoryBatch.medication_product_id == product_id)

    results = query.all()

    stock_levels = []
    for result in results:
        # Get location details
        location = db.query(InventoryLocation).filter(InventoryLocation.id == result.location_id).first()

        # Get batches for this location/product combo
        batches = db.query(InventoryBatch).filter(
            InventoryBatch.location_id == result.location_id,
            InventoryBatch.medication_product_id == result.medication_product_id
        ).all()

        # Get a sample batch for unit
        sample_batch = batches[0] if batches else None

        stock_levels.append({
            "location_id": result.location_id,
            "location_name": location.name if location else "Unknown",
            "medication_product_id": result.medication_product_id,
            "total_quantity": float(result.total_quantity),
            "quantity_unit": sample_batch.quantity_unit if sample_batch else None,
            "batches": batches
        })

    return stock_levels

# Vendor Endpoints
@app.post("/api/v1/pharmacy/vendors", response_model=VendorResponse, status_code=201, tags=["Vendors"])
async def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a vendor"""
    vendor = Vendor(
        tenant_id=vendor_data.tenant_id,
        name=vendor_data.name,
        code=vendor_data.code,
        contact_details=vendor_data.contact_details,
        is_active=vendor_data.is_active
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    logger.info(f"Vendor created: {vendor.name}")
    return vendor

@app.get("/api/v1/pharmacy/vendors", response_model=List[VendorResponse], tags=["Vendors"])
async def list_vendors(
    tenant_id: UUID = Query(...),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List vendors"""
    query = db.query(Vendor).filter(Vendor.tenant_id == tenant_id)

    if is_active is not None:
        query = query.filter(Vendor.is_active == is_active)

    return query.order_by(Vendor.name).all()

# Purchase Order Endpoints
@app.post("/api/v1/pharmacy/purchase-orders", response_model=PurchaseOrderResponse, status_code=201, tags=["Purchase Orders"])
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    lines: List[PurchaseOrderLineCreate],
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a purchase order with line items"""
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == po_data.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Check for duplicate PO number
    existing = db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == po_data.tenant_id,
        PurchaseOrder.po_number == po_data.po_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="PO number already exists for this tenant")

    purchase_order = PurchaseOrder(
        tenant_id=po_data.tenant_id,
        vendor_id=po_data.vendor_id,
        po_number=po_data.po_number,
        status='draft',
        expected_delivery_date=po_data.expected_delivery_date,
        created_by_user_id=current_user_id
    )
    db.add(purchase_order)
    db.flush()  # Get PO ID

    # Create line items
    for line_data in lines:
        # Verify product exists
        product = db.query(MedicationProduct).filter(MedicationProduct.id == line_data.medication_product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Medication product not found: {line_data.medication_product_id}")

        line = PurchaseOrderLine(
            purchase_order_id=purchase_order.id,
            medication_product_id=line_data.medication_product_id,
            quantity_ordered=line_data.quantity_ordered,
            quantity_unit=line_data.quantity_unit,
            unit_price=line_data.unit_price
        )
        db.add(line)

    db.commit()
    db.refresh(purchase_order)

    await publish_event(EventType.PURCHASE_ORDER_CREATED, {
        "purchase_order_id": str(purchase_order.id),
        "vendor_id": str(purchase_order.vendor_id),
        "po_number": purchase_order.po_number,
        "line_count": len(lines)
    })

    logger.info(f"Purchase order created: {purchase_order.po_number}")
    return purchase_order

@app.get("/api/v1/pharmacy/purchase-orders", response_model=List[PurchaseOrderResponse], tags=["Purchase Orders"])
async def list_purchase_orders(
    tenant_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    vendor_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List purchase orders"""
    query = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id)

    if status:
        query = query.filter(PurchaseOrder.status == status)
    if vendor_id:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)

    return query.order_by(PurchaseOrder.created_at.desc()).all()

@app.get("/api/v1/pharmacy/purchase-orders/{po_id}", response_model=PurchaseOrderResponse, tags=["Purchase Orders"])
async def get_purchase_order(po_id: UUID, db: Session = Depends(get_db)):
    """Get purchase order details"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@app.get("/api/v1/pharmacy/purchase-orders/{po_id}/lines", response_model=List[PurchaseOrderLineResponse], tags=["Purchase Orders"])
async def get_purchase_order_lines(po_id: UUID, db: Session = Depends(get_db)):
    """Get purchase order line items"""
    return db.query(PurchaseOrderLine).filter(
        PurchaseOrderLine.purchase_order_id == po_id
    ).all()

@app.post("/api/v1/pharmacy/purchase-orders/{po_id}/receive", response_model=PurchaseOrderResponse, tags=["Purchase Orders"])
async def receive_purchase_order(
    po_id: UUID,
    location_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Receive a purchase order
    Creates inventory batches and transactions for all line items
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po.status == 'completed':
        raise HTTPException(status_code=400, detail="Purchase order already completed")

    # Verify location exists
    location = db.query(InventoryLocation).filter(InventoryLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Get all lines
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po_id).all()

    for line in lines:
        # Create inventory batch
        batch = InventoryBatch(
            tenant_id=po.tenant_id,
            medication_product_id=line.medication_product_id,
            batch_number=f"PO-{po.po_number}",
            current_quantity=line.quantity_ordered,
            quantity_unit=line.quantity_unit,
            location_id=location_id
        )
        db.add(batch)
        db.flush()

        # Create transaction
        transaction = InventoryTransaction(
            tenant_id=po.tenant_id,
            inventory_batch_id=batch.id,
            transaction_type='receive',
            quantity_delta=line.quantity_ordered,
            reason=f"Received from PO {po.po_number}",
            related_purchase_order_line_id=line.id,
            created_by_user_id=current_user_id
        )
        db.add(transaction)

        # Update line quantity received
        line.quantity_received = line.quantity_ordered
        line.updated_at = datetime.utcnow()

    # Update PO status
    po.status = 'completed'
    po.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(po)

    await publish_event(EventType.PURCHASE_ORDER_RECEIVED, {
        "purchase_order_id": str(po.id),
        "po_number": po.po_number,
        "location_id": str(location_id),
        "received_by": str(current_user_id) if current_user_id else None
    })

    logger.info(f"Purchase order received: {po.po_number}")
    return po

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "pharmacy-inventory-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8048)
