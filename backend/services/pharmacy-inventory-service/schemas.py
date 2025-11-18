"""Pharmacy Inventory Service Schemas"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# Inventory Location Schemas
class InventoryLocationCreate(BaseModel):
    tenant_id: UUID
    code: str
    name: str
    type: str = Field(..., description="pharmacy_store, ward_cupboard")
    is_active: bool = True

class InventoryLocationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Inventory Batch Schemas
class InventoryBatchCreate(BaseModel):
    tenant_id: UUID
    medication_product_id: UUID
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    current_quantity: float
    quantity_unit: Optional[str] = None
    location_id: UUID

class InventoryBatchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    medication_product_id: UUID
    batch_number: Optional[str]
    expiry_date: Optional[date]
    current_quantity: float
    quantity_unit: Optional[str]
    location_id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Inventory Transaction Schemas
class InventoryTransactionCreate(BaseModel):
    inventory_batch_id: UUID
    transaction_type: str = Field(..., description="receive, dispense, transfer_out, transfer_in, adjustment, return")
    quantity_delta: float
    reason: Optional[str] = None
    related_dispensation_id: Optional[UUID] = None
    related_purchase_order_line_id: Optional[UUID] = None

class InventoryTransactionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    inventory_batch_id: UUID
    transaction_type: str
    quantity_delta: float
    reason: Optional[str]
    related_dispensation_id: Optional[UUID]
    related_purchase_order_line_id: Optional[UUID]
    created_at: datetime
    created_by_user_id: Optional[UUID]
    class Config:
        from_attributes = True

# Vendor Schemas
class VendorCreate(BaseModel):
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    contact_details: Optional[Dict[str, Any]] = None
    is_active: bool = True

class VendorResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str]
    contact_details: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Purchase Order Schemas
class PurchaseOrderCreate(BaseModel):
    tenant_id: UUID
    vendor_id: UUID
    po_number: str
    expected_delivery_date: Optional[date] = None

class PurchaseOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    po_number: str
    status: str
    ordered_at: Optional[datetime]
    expected_delivery_date: Optional[date]
    created_by_user_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Purchase Order Line Schemas
class PurchaseOrderLineCreate(BaseModel):
    medication_product_id: UUID
    quantity_ordered: float
    quantity_unit: Optional[str] = None
    unit_price: Optional[float] = None

class PurchaseOrderLineResponse(BaseModel):
    id: UUID
    purchase_order_id: UUID
    medication_product_id: UUID
    quantity_ordered: float
    quantity_received: float
    quantity_unit: Optional[str]
    unit_price: Optional[float]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Stock Level Response
class StockLevelResponse(BaseModel):
    location_id: UUID
    location_name: str
    medication_product_id: UUID
    total_quantity: float
    quantity_unit: Optional[str]
    batches: List[InventoryBatchResponse]
