"""
Governance & Audit Service
LLM session tracking, tool call logging, response monitoring, and policy violation management

Port: 8019
Endpoints: 7 (LLM Sessions, Tool Calls, Responses, Policy Violations)
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import logging
import os

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_, func, desc
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

# Import shared models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database.models import (
    Base, LLMSession, LLMToolCall, LLMResponse, PolicyViolation,
    User, Patient, Encounter
)
from shared.events.publisher import publish_event, EventType

# Import schemas
from schemas import (
    LLMSessionCreate, LLMSessionResponse, EndSessionRequest, LLMSessionListResponse,
    LLMToolCallCreate, LLMToolCallResponse,
    LLMResponseCreate, LLMResponseResponse,
    PolicyViolationCreate, PolicyViolationUpdate, PolicyViolationResponse, PolicyViolationListResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthtech:healthtech123@localhost:5432/healthtech_db"
)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Governance & Audit Service",
    description="LLM session tracking, tool call logging, and policy violation management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# Dependencies
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Helper Functions ====================

def calculate_token_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate estimated cost in USD based on token usage

    Pricing (simplified, would be loaded from config):
    - GPT-4: $0.03 / 1K prompt, $0.06 / 1K completion
    - GPT-3.5: $0.001 / 1K prompt, $0.002 / 1K completion
    - Claude 3 Opus: $0.015 / 1K prompt, $0.075 / 1K completion
    """
    pricing = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    }

    # Default pricing if model not found
    default_pricing = {"prompt": 0.01, "completion": 0.03}

    model_pricing = pricing.get(model_name.lower(), default_pricing)

    prompt_cost = (prompt_tokens / 1000) * model_pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * model_pricing["completion"]

    return round(prompt_cost + completion_cost, 6)


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "governance-audit-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== LLM Session Endpoints ====================

@app.post("/api/v1/governance/llm-sessions", response_model=LLMSessionResponse, status_code=201)
async def create_llm_session(
    session_data: LLMSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Start a new LLM session for governance tracking

    - Tracks all AI interactions
    - Records system prompts and safety config
    - Links to user, patient, encounter
    - Publishes LLM_SESSION_STARTED event

    **Use Cases:**
    - Medical scribe sessions
    - Care coordinator AI agents
    - Clinical decision support
    - Discharge planning assistants
    - Radiology report generation
    - ICD coding assistance
    """
    try:
        # Validate user if provided
        if session_data.user_id:
            user = db.query(User).filter(User.id == session_data.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

        # Validate patient if provided
        if session_data.patient_id:
            patient = db.query(Patient).filter(Patient.id == session_data.patient_id).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")

        # Validate encounter if provided
        if session_data.encounter_id:
            encounter = db.query(Encounter).filter(Encounter.id == session_data.encounter_id).first()
            if not encounter:
                raise HTTPException(status_code=404, detail="Encounter not found")

        # Create LLM session
        llm_session = LLMSession(
            tenant_id=session_data.tenant_id,
            user_id=session_data.user_id,
            patient_id=session_data.patient_id,
            encounter_id=session_data.encounter_id,
            session_type=session_data.session_type,
            model_name=session_data.model_name,
            model_version=session_data.model_version,
            system_prompt=session_data.system_prompt,
            initial_context=session_data.initial_context,
            safety_config=session_data.safety_config,
            started_at=datetime.utcnow(),
            tool_call_count=0,
            response_count=0,
            violation_count=0,
            created_at=datetime.utcnow()
        )

        db.add(llm_session)
        db.commit()
        db.refresh(llm_session)

        # Publish event
        await publish_event(
            EventType.LLM_SESSION_STARTED,
            {
                "session_id": str(llm_session.id),
                "tenant_id": str(llm_session.tenant_id),
                "session_type": llm_session.session_type,
                "model_name": llm_session.model_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Started LLM session: {llm_session.id} - Type: {llm_session.session_type}")
        return llm_session

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating LLM session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/governance/llm-sessions/{session_id}/end", response_model=LLMSessionResponse)
async def end_llm_session(
    session_id: UUID,
    end_request: EndSessionRequest,
    db: Session = Depends(get_db)
):
    """
    End an LLM session

    - Marks session as completed
    - Calculates total tokens and cost
    - Records session outcome
    - Publishes LLM_SESSION_ENDED event
    """
    try:
        # Get session
        session = db.query(LLMSession).filter(LLMSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="LLM session not found")

        if session.ended_at:
            raise HTTPException(status_code=400, detail="Session already ended")

        # Calculate total tokens from all responses
        total_tokens = db.query(func.sum(LLMResponse.total_tokens)).filter(
            LLMResponse.llm_session_id == session_id
        ).scalar() or 0

        # Get sum of prompt and completion tokens separately for cost calculation
        token_sums = db.query(
            func.sum(LLMResponse.prompt_tokens).label("prompt_tokens"),
            func.sum(LLMResponse.completion_tokens).label("completion_tokens")
        ).filter(LLMResponse.llm_session_id == session_id).first()

        prompt_tokens = token_sums.prompt_tokens or 0
        completion_tokens = token_sums.completion_tokens or 0

        # Calculate cost
        total_cost = calculate_token_cost(session.model_name, prompt_tokens, completion_tokens)

        # End session
        session.ended_at = datetime.utcnow()
        session.total_tokens = total_tokens
        session.total_cost_usd = total_cost

        db.commit()
        db.refresh(session)

        # Publish event
        await publish_event(
            EventType.LLM_SESSION_ENDED,
            {
                "session_id": str(session.id),
                "tenant_id": str(session.tenant_id),
                "session_type": session.session_type,
                "total_tokens": session.total_tokens,
                "total_cost_usd": session.total_cost_usd,
                "outcome": end_request.outcome,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Ended LLM session: {session_id} - Tokens: {total_tokens}, Cost: ${total_cost}")
        return session

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error ending LLM session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/governance/llm-sessions", response_model=LLMSessionListResponse)
async def list_llm_sessions(
    tenant_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    session_type: Optional[str] = Query(None),
    model_name: Optional[str] = Query(None),
    started_after: Optional[datetime] = Query(None),
    started_before: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List LLM sessions with filtering

    - Filter by tenant, user, patient, session type, model
    - Time range filtering
    - Paginated results
    - Ordered by started_at descending

    **Use Cases:**
    - Audit all AI interactions for a patient
    - Track usage by user or model
    - Monitor AI agent performance
    - Cost analysis and billing
    """
    try:
        # Build base query
        query = db.query(LLMSession)

        # Apply filters
        if tenant_id:
            query = query.filter(LLMSession.tenant_id == tenant_id)
        if user_id:
            query = query.filter(LLMSession.user_id == user_id)
        if patient_id:
            query = query.filter(LLMSession.patient_id == patient_id)
        if session_type:
            query = query.filter(LLMSession.session_type == session_type.lower())
        if model_name:
            query = query.filter(LLMSession.model_name.ilike(f"%{model_name}%"))
        if started_after:
            query = query.filter(LLMSession.started_at >= started_after)
        if started_before:
            query = query.filter(LLMSession.started_at <= started_before)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        sessions = query.order_by(desc(LLMSession.started_at)).offset(offset).limit(page_size).all()

        return LLMSessionListResponse(
            total=total,
            sessions=sessions,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing LLM sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Tool Call Endpoint ====================

@app.post("/api/v1/governance/llm-sessions/{session_id}/tool-calls", response_model=LLMToolCallResponse, status_code=201)
async def log_tool_call(
    session_id: UUID,
    tool_call: LLMToolCallCreate,
    db: Session = Depends(get_db)
):
    """
    Log an LLM tool call

    - Tracks which tools AI agents use
    - Records arguments and results
    - Monitors latency
    - Enables explainability ("why did AI do X?")
    - Publishes LLM_TOOL_CALLED event

    **Tracked Information:**
    - Tool name and arguments
    - Execution result
    - Latency in milliseconds
    - Success/failure status
    - Errors if any
    """
    try:
        # Validate session exists
        session = db.query(LLMSession).filter(LLMSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="LLM session not found")

        # Create tool call record
        tool_call_record = LLMToolCall(
            llm_session_id=session_id,
            tool_name=tool_call.tool_name,
            tool_args=tool_call.tool_args,
            tool_result=tool_call.tool_result,
            latency_ms=tool_call.latency_ms,
            success=tool_call.success,
            error_message=tool_call.error_message,
            created_at=datetime.utcnow()
        )

        db.add(tool_call_record)

        # Update session tool call count
        session.tool_call_count = (session.tool_call_count or 0) + 1

        db.commit()
        db.refresh(tool_call_record)

        # Publish event
        await publish_event(
            EventType.LLM_TOOL_CALLED,
            {
                "tool_call_id": str(tool_call_record.id),
                "session_id": str(session_id),
                "tenant_id": str(session.tenant_id),
                "tool_name": tool_call.tool_name,
                "success": tool_call.success,
                "latency_ms": tool_call.latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Logged tool call: {tool_call.tool_name} for session {session_id}")
        return tool_call_record

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging tool call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LLM Response Endpoint ====================

@app.post("/api/v1/governance/llm-sessions/{session_id}/responses", response_model=LLMResponseResponse, status_code=201)
async def log_llm_response(
    session_id: UUID,
    response_data: LLMResponseCreate,
    db: Session = Depends(get_db)
):
    """
    Log an LLM response

    - Tracks prompts and completions
    - Records token usage for billing
    - Monitors latency
    - Captures safety flags
    - Enables session replay

    **Tracked Information:**
    - Full prompt and response text
    - Token counts (prompt, completion, total)
    - Generation latency
    - Finish reason (stop, length, content_filter)
    - Safety flags (PII, toxicity, etc.)
    - Model parameters (temperature, top_p)
    """
    try:
        # Validate session exists
        session = db.query(LLMSession).filter(LLMSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="LLM session not found")

        # Create response record
        llm_response = LLMResponse(
            llm_session_id=session_id,
            prompt=response_data.prompt,
            response=response_data.response,
            prompt_tokens=response_data.prompt_tokens,
            completion_tokens=response_data.completion_tokens,
            total_tokens=response_data.total_tokens,
            latency_ms=response_data.latency_ms,
            finish_reason=response_data.finish_reason,
            safety_flags=response_data.safety_flags,
            model_metadata=response_data.model_metadata,
            created_at=datetime.utcnow()
        )

        db.add(llm_response)

        # Update session response count
        session.response_count = (session.response_count or 0) + 1

        db.commit()
        db.refresh(llm_response)

        logger.info(f"Logged LLM response for session {session_id} - Tokens: {response_data.total_tokens}")
        return llm_response

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging LLM response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Policy Violation Endpoints ====================

@app.post("/api/v1/governance/llm-sessions/{session_id}/policy-violations", response_model=PolicyViolationResponse, status_code=201)
async def report_policy_violation(
    session_id: UUID,
    violation_data: PolicyViolationCreate,
    db: Session = Depends(get_db)
):
    """
    Report a policy violation

    - Tracks safety issues
    - Records PII exposures
    - Flags hallucinations
    - Detects unsafe recommendations
    - Monitors policy breaches
    - Publishes POLICY_VIOLATION_DETECTED event

    **Violation Types:**
    - PII exposure: Patient data leaked in response
    - Toxicity: Inappropriate language
    - Hallucination: Factually incorrect information
    - Unsafe recommendation: Dangerous clinical advice
    - Policy breach: Violation of hospital policies
    - Data leak: Unauthorized data disclosure
    - Bias: Discriminatory content
    """
    try:
        # Validate session exists
        session = db.query(LLMSession).filter(LLMSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="LLM session not found")

        # Create violation record
        violation = PolicyViolation(
            tenant_id=session.tenant_id,
            llm_session_id=session_id,
            violation_type=violation_data.violation_type,
            severity=violation_data.severity,
            description=violation_data.description,
            detected_by=violation_data.detected_by,
            evidence=violation_data.evidence,
            mitigation_action=violation_data.mitigation_action,
            resolution_status="open",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(violation)

        # Update session violation count
        session.violation_count = (session.violation_count or 0) + 1

        db.commit()
        db.refresh(violation)

        # Publish event
        await publish_event(
            EventType.POLICY_VIOLATION_DETECTED,
            {
                "violation_id": str(violation.id),
                "session_id": str(session_id),
                "tenant_id": str(session.tenant_id),
                "violation_type": violation.violation_type,
                "severity": violation.severity,
                "detected_by": violation.detected_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.warning(f"Policy violation detected: {violation.violation_type} - Severity: {violation.severity}")
        return violation

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reporting policy violation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/governance/policy-violations", response_model=PolicyViolationListResponse)
async def list_policy_violations(
    tenant_id: Optional[UUID] = Query(None),
    session_id: Optional[UUID] = Query(None),
    violation_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resolution_status: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List policy violations with filtering

    - Filter by tenant, session, type, severity, status
    - Time range filtering
    - Paginated results
    - Ordered by created_at descending (newest first)

    **Use Cases:**
    - Safety monitoring dashboard
    - Compliance reporting
    - Incident investigation
    - Model fine-tuning feedback
    """
    try:
        # Build base query
        query = db.query(PolicyViolation)

        # Apply filters
        if tenant_id:
            query = query.filter(PolicyViolation.tenant_id == tenant_id)
        if session_id:
            query = query.filter(PolicyViolation.llm_session_id == session_id)
        if violation_type:
            query = query.filter(PolicyViolation.violation_type == violation_type.lower())
        if severity:
            query = query.filter(PolicyViolation.severity == severity.lower())
        if resolution_status:
            query = query.filter(PolicyViolation.resolution_status == resolution_status.lower())
        if created_after:
            query = query.filter(PolicyViolation.created_at >= created_after)
        if created_before:
            query = query.filter(PolicyViolation.created_at <= created_before)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        violations = query.order_by(desc(PolicyViolation.created_at)).offset(offset).limit(page_size).all()

        return PolicyViolationListResponse(
            total=total,
            violations=violations,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing policy violations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8019)
