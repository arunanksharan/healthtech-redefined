"""
Knowledge Graph Service - Port 8030
Medical knowledge graph for concept relationships and patient-specific graph traversal
"""
import logging
from datetime import datetime
from typing import List, Optional, Set
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    KGNode, KGEdge, PatientKGNode, PatientKGEdge, Patient, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    KGNodeCreate, KGNodeResponse,
    KGEdgeCreate, KGEdgeResponse,
    PatientKGNodeCreate, PatientKGNodeResponse,
    PatientKGEdgeCreate, PatientKGEdgeResponse,
    GraphTraversalRequest, GraphTraversalResponse,
    PatientGraphQueryRequest, PatientGraphQueryResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Knowledge Graph Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Global KG Node Endpoints
@app.post("/api/v1/kg/nodes", response_model=KGNodeResponse, status_code=201, tags=["Global KG"])
async def create_kg_node(
    node_data: KGNodeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a global medical concept node"""
    # Check for duplicate code in code_system
    existing = db.query(KGNode).filter(and_(
        KGNode.code_system == node_data.code_system,
        KGNode.code == node_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Node with this code already exists in code system")

    node = KGNode(
        code_system=node_data.code_system,
        code=node_data.code,
        label=node_data.label,
        node_type=node_data.node_type,
        properties=node_data.properties
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    await publish_event(EventType.KG_NODE_CREATED, {
        "node_id": str(node.id),
        "code_system": node.code_system,
        "code": node.code,
        "label": node.label,
        "node_type": node.node_type
    })

    logger.info(f"KG node created: {node.code_system}:{node.code}")
    return node

@app.get("/api/v1/kg/nodes", response_model=List[KGNodeResponse], tags=["Global KG"])
async def list_kg_nodes(
    code_system: Optional[str] = Query(None),
    node_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search in label or code"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """List global medical concept nodes with filters"""
    query = db.query(KGNode)

    if code_system:
        query = query.filter(KGNode.code_system == code_system)
    if node_type:
        query = query.filter(KGNode.node_type == node_type)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            KGNode.label.ilike(search_term),
            KGNode.code.ilike(search_term)
        ))

    return query.limit(limit).all()

@app.get("/api/v1/kg/nodes/{node_id}", response_model=KGNodeResponse, tags=["Global KG"])
async def get_kg_node(node_id: UUID, db: Session = Depends(get_db)):
    """Get global KG node details"""
    node = db.query(KGNode).filter(KGNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="KG node not found")
    return node

# Global KG Edge Endpoints
@app.post("/api/v1/kg/edges", response_model=KGEdgeResponse, status_code=201, tags=["Global KG"])
async def create_kg_edge(
    edge_data: KGEdgeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create a relationship between global medical concepts"""
    # Verify both nodes exist
    source = db.query(KGNode).filter(KGNode.id == edge_data.source_node_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source node not found")

    target = db.query(KGNode).filter(KGNode.id == edge_data.target_node_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target node not found")

    edge = KGEdge(
        source_node_id=edge_data.source_node_id,
        target_node_id=edge_data.target_node_id,
        relationship_type=edge_data.relationship_type,
        weight=edge_data.weight,
        evidence_level=edge_data.evidence_level,
        properties=edge_data.properties
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    await publish_event(EventType.KG_EDGE_CREATED, {
        "edge_id": str(edge.id),
        "source_node_id": str(edge.source_node_id),
        "target_node_id": str(edge.target_node_id),
        "relationship_type": edge.relationship_type
    })

    logger.info(f"KG edge created: {edge.relationship_type}")
    return edge

@app.get("/api/v1/kg/edges", response_model=List[KGEdgeResponse], tags=["Global KG"])
async def list_kg_edges(
    source_node_id: Optional[UUID] = Query(None),
    target_node_id: Optional[UUID] = Query(None),
    relationship_type: Optional[str] = Query(None),
    min_weight: Optional[float] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """List global KG edges with filters"""
    query = db.query(KGEdge)

    if source_node_id:
        query = query.filter(KGEdge.source_node_id == source_node_id)
    if target_node_id:
        query = query.filter(KGEdge.target_node_id == target_node_id)
    if relationship_type:
        query = query.filter(KGEdge.relationship_type == relationship_type)
    if min_weight is not None:
        query = query.filter(KGEdge.weight >= min_weight)

    return query.limit(limit).all()

# Graph Traversal
@app.post("/api/v1/kg/traverse", response_model=GraphTraversalResponse, tags=["Global KG"])
async def traverse_graph(
    traversal_request: GraphTraversalRequest,
    db: Session = Depends(get_db)
):
    """
    Traverse the global knowledge graph from a starting node
    Returns nodes, edges, and paths within max_depth
    """
    start_node = db.query(KGNode).filter(KGNode.id == traversal_request.start_node_id).first()
    if not start_node:
        raise HTTPException(status_code=404, detail="Start node not found")

    visited_nodes: Set[UUID] = set()
    visited_edges: Set[UUID] = set()
    paths: List[List[UUID]] = []

    def traverse(node_id: UUID, current_path: List[UUID], depth: int):
        if depth > traversal_request.max_depth:
            return

        visited_nodes.add(node_id)
        current_path.append(node_id)

        if len(current_path) > 1:
            paths.append(current_path.copy())

        # Get edges based on direction
        edges_query = db.query(KGEdge)

        if traversal_request.direction in ['outgoing', 'both']:
            outgoing = edges_query.filter(KGEdge.source_node_id == node_id)
            if traversal_request.relationship_types:
                outgoing = outgoing.filter(KGEdge.relationship_type.in_(traversal_request.relationship_types))
            if traversal_request.min_weight is not None:
                outgoing = outgoing.filter(KGEdge.weight >= traversal_request.min_weight)

            for edge in outgoing.all():
                visited_edges.add(edge.id)
                if edge.target_node_id not in visited_nodes:
                    traverse(edge.target_node_id, current_path.copy(), depth + 1)

        if traversal_request.direction in ['incoming', 'both']:
            incoming = edges_query.filter(KGEdge.target_node_id == node_id)
            if traversal_request.relationship_types:
                incoming = incoming.filter(KGEdge.relationship_type.in_(traversal_request.relationship_types))
            if traversal_request.min_weight is not None:
                incoming = incoming.filter(KGEdge.weight >= traversal_request.min_weight)

            for edge in incoming.all():
                visited_edges.add(edge.id)
                if edge.source_node_id not in visited_nodes:
                    traverse(edge.source_node_id, current_path.copy(), depth + 1)

    # Start traversal
    traverse(traversal_request.start_node_id, [], 0)

    # Get all visited nodes and edges
    nodes = db.query(KGNode).filter(KGNode.id.in_(visited_nodes)).all()
    edges = db.query(KGEdge).filter(KGEdge.id.in_(visited_edges)).all()

    logger.info(f"Graph traversal: {len(nodes)} nodes, {len(edges)} edges, {len(paths)} paths")

    return GraphTraversalResponse(
        nodes=nodes,
        edges=edges,
        paths=paths
    )

# Patient KG Node Endpoints
@app.post("/api/v1/kg/patient-nodes", response_model=PatientKGNodeResponse, status_code=201, tags=["Patient KG"])
async def create_patient_kg_node(
    node_data: PatientKGNodeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create patient-specific instance of a global concept"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == node_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify global KG node exists
    kg_node = db.query(KGNode).filter(KGNode.id == node_data.kg_node_id).first()
    if not kg_node:
        raise HTTPException(status_code=404, detail="Global KG node not found")

    patient_node = PatientKGNode(
        patient_id=node_data.patient_id,
        kg_node_id=node_data.kg_node_id,
        occurred_at=node_data.occurred_at,
        context=node_data.context,
        confidence=node_data.confidence,
        properties=node_data.properties
    )
    db.add(patient_node)
    db.commit()
    db.refresh(patient_node)

    await publish_event(EventType.PATIENT_KG_UPDATED, {
        "patient_id": str(patient.id),
        "patient_kg_node_id": str(patient_node.id),
        "kg_node_id": str(kg_node.id),
        "concept": f"{kg_node.code_system}:{kg_node.code}"
    })

    logger.info(f"Patient KG node created for patient {patient.id}")
    return patient_node

@app.get("/api/v1/kg/patient-nodes", response_model=List[PatientKGNodeResponse], tags=["Patient KG"])
async def list_patient_kg_nodes(
    patient_id: UUID,
    kg_node_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List patient-specific KG nodes"""
    query = db.query(PatientKGNode).filter(PatientKGNode.patient_id == patient_id)

    if kg_node_id:
        query = query.filter(PatientKGNode.kg_node_id == kg_node_id)
    if start_date:
        query = query.filter(PatientKGNode.occurred_at >= start_date)
    if end_date:
        query = query.filter(PatientKGNode.occurred_at <= end_date)

    return query.order_by(PatientKGNode.occurred_at.desc()).all()

# Patient KG Edge Endpoints
@app.post("/api/v1/kg/patient-edges", response_model=PatientKGEdgeResponse, status_code=201, tags=["Patient KG"])
async def create_patient_kg_edge(
    edge_data: PatientKGEdgeCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create relationship between patient-specific concept instances"""
    # Verify both patient nodes exist and belong to same patient
    source = db.query(PatientKGNode).filter(PatientKGNode.id == edge_data.source_patient_kg_node_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source patient KG node not found")

    target = db.query(PatientKGNode).filter(PatientKGNode.id == edge_data.target_patient_kg_node_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target patient KG node not found")

    if source.patient_id != edge_data.patient_id or target.patient_id != edge_data.patient_id:
        raise HTTPException(status_code=400, detail="Patient nodes must belong to the specified patient")

    patient_edge = PatientKGEdge(
        patient_id=edge_data.patient_id,
        source_patient_kg_node_id=edge_data.source_patient_kg_node_id,
        target_patient_kg_node_id=edge_data.target_patient_kg_node_id,
        relationship_type=edge_data.relationship_type,
        confidence=edge_data.confidence,
        inferred_by=edge_data.inferred_by,
        properties=edge_data.properties
    )
    db.add(patient_edge)
    db.commit()
    db.refresh(patient_edge)

    logger.info(f"Patient KG edge created for patient {edge_data.patient_id}")
    return patient_edge

@app.get("/api/v1/kg/patient-edges", response_model=List[PatientKGEdgeResponse], tags=["Patient KG"])
async def list_patient_kg_edges(
    patient_id: UUID,
    relationship_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List patient-specific KG edges"""
    query = db.query(PatientKGEdge).filter(PatientKGEdge.patient_id == patient_id)

    if relationship_type:
        query = query.filter(PatientKGEdge.relationship_type == relationship_type)

    return query.all()

# Patient Graph Query
@app.post("/api/v1/kg/patient-graph", response_model=PatientGraphQueryResponse, tags=["Patient KG"])
async def query_patient_graph(
    query_request: PatientGraphQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query complete patient knowledge graph
    Returns patient-specific nodes/edges with optional global context
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == query_request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get patient nodes
    patient_nodes_query = db.query(PatientKGNode).filter(PatientKGNode.patient_id == query_request.patient_id)

    if query_request.start_date:
        patient_nodes_query = patient_nodes_query.filter(PatientKGNode.occurred_at >= query_request.start_date)
    if query_request.end_date:
        patient_nodes_query = patient_nodes_query.filter(PatientKGNode.occurred_at <= query_request.end_date)

    patient_nodes = patient_nodes_query.all()

    # Filter by node types if specified
    if query_request.node_types and query_request.include_global_context:
        kg_node_ids = [pn.kg_node_id for pn in patient_nodes]
        global_nodes = db.query(KGNode).filter(and_(
            KGNode.id.in_(kg_node_ids),
            KGNode.node_type.in_(query_request.node_types)
        )).all()

        # Filter patient nodes to match
        valid_kg_node_ids = {gn.id for gn in global_nodes}
        patient_nodes = [pn for pn in patient_nodes if pn.kg_node_id in valid_kg_node_ids]

    # Get patient edges
    patient_edges_query = db.query(PatientKGEdge).filter(PatientKGEdge.patient_id == query_request.patient_id)

    if query_request.relationship_types:
        patient_edges_query = patient_edges_query.filter(
            PatientKGEdge.relationship_type.in_(query_request.relationship_types)
        )

    patient_edges = patient_edges_query.all()

    # Get global context if requested
    global_nodes = None
    global_edges = None

    if query_request.include_global_context:
        kg_node_ids = list(set([pn.kg_node_id for pn in patient_nodes]))
        global_nodes = db.query(KGNode).filter(KGNode.id.in_(kg_node_ids)).all()

        # Get edges between these global nodes
        global_edges = db.query(KGEdge).filter(or_(
            and_(KGEdge.source_node_id.in_(kg_node_ids), KGEdge.target_node_id.in_(kg_node_ids))
        )).all()

    await publish_event(EventType.KG_TRAVERSAL_EXECUTED, {
        "patient_id": str(query_request.patient_id),
        "patient_nodes_count": len(patient_nodes),
        "patient_edges_count": len(patient_edges),
        "global_nodes_count": len(global_nodes) if global_nodes else 0
    })

    logger.info(f"Patient graph queried: {len(patient_nodes)} patient nodes, {len(patient_edges)} patient edges")

    return PatientGraphQueryResponse(
        patient_nodes=patient_nodes,
        patient_edges=patient_edges,
        global_nodes=global_nodes,
        global_edges=global_edges
    )

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "knowledge-graph-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8030)
