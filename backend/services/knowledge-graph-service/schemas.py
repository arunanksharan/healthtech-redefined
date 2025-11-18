"""Knowledge Graph Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

# KG Node Schemas (Global Concepts)
class KGNodeCreate(BaseModel):
    code_system: str = Field(..., description="SNOMED, ICD10, LOINC, RXNORM")
    code: str
    label: str
    node_type: str = Field(..., description="condition, lab, medication, procedure")
    properties: Optional[Dict[str, Any]] = None

class KGNodeResponse(BaseModel):
    id: UUID
    code_system: str
    code: str
    label: str
    node_type: str
    properties: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# KG Edge Schemas (Global Relationships)
class KGEdgeCreate(BaseModel):
    source_node_id: UUID
    target_node_id: UUID
    relationship_type: str = Field(..., description="associated_with, treats, contraindicates")
    weight: Optional[float] = Field(None, description="Strength of relationship 0-1")
    evidence_level: Optional[str] = Field(None, description="RCT, observational, guideline")
    properties: Optional[Dict[str, Any]] = None

class KGEdgeResponse(BaseModel):
    id: UUID
    source_node_id: UUID
    target_node_id: UUID
    relationship_type: str
    weight: Optional[float]
    evidence_level: Optional[str]
    properties: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Patient KG Node Schemas (Patient-Specific Instances)
class PatientKGNodeCreate(BaseModel):
    patient_id: UUID
    kg_node_id: UUID
    occurred_at: datetime
    context: Optional[str] = Field(None, description="encounter_id, observation_id, etc")
    confidence: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None

class PatientKGNodeResponse(BaseModel):
    id: UUID
    patient_id: UUID
    kg_node_id: UUID
    occurred_at: datetime
    context: Optional[str]
    confidence: Optional[float]
    properties: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Patient KG Edge Schemas (Patient-Specific Relationships)
class PatientKGEdgeCreate(BaseModel):
    patient_id: UUID
    source_patient_kg_node_id: UUID
    target_patient_kg_node_id: UUID
    relationship_type: str = Field(..., description="temporal_before, caused_by, causal_suspected")
    confidence: Optional[float] = None
    inferred_by: Optional[str] = Field(None, description="clinician, llm, rule_engine")
    properties: Optional[Dict[str, Any]] = None

class PatientKGEdgeResponse(BaseModel):
    id: UUID
    patient_id: UUID
    source_patient_kg_node_id: UUID
    target_patient_kg_node_id: UUID
    relationship_type: str
    confidence: Optional[float]
    inferred_by: Optional[str]
    properties: Optional[Dict[str, Any]]
    created_at: datetime
    class Config:
        from_attributes = True

# Graph Traversal Schemas
class GraphTraversalRequest(BaseModel):
    start_node_id: UUID
    relationship_types: Optional[List[str]] = Field(None, description="Filter by relationship types")
    max_depth: int = Field(default=3, description="Maximum traversal depth")
    direction: str = Field(default='both', description="outgoing, incoming, both")
    min_weight: Optional[float] = Field(None, description="Minimum edge weight")

class GraphTraversalResponse(BaseModel):
    nodes: List[KGNodeResponse]
    edges: List[KGEdgeResponse]
    paths: List[List[UUID]] = Field(..., description="Paths from start node")

# Patient Graph Query Schema
class PatientGraphQueryRequest(BaseModel):
    patient_id: UUID
    node_types: Optional[List[str]] = Field(None, description="Filter by node types")
    relationship_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_global_context: bool = Field(
        default=True,
        description="Include global KG relationships for patient nodes"
    )

class PatientGraphQueryResponse(BaseModel):
    patient_nodes: List[PatientKGNodeResponse]
    patient_edges: List[PatientKGEdgeResponse]
    global_nodes: Optional[List[KGNodeResponse]] = None
    global_edges: Optional[List[KGEdgeResponse]] = None
