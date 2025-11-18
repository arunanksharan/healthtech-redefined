"""
Voice & Collaboration Service
Real-time voice transcription (ASR), multi-user collaboration, and note versioning

Port: 8018
Endpoints: 12 (Voice Sessions, Collaboration Threads, Note Revisions)
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import logging
import os

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_, func, desc
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError

# Import shared models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from shared.database.models import (
    Base, VoiceSession, VoiceSegment, CollabThread, CollabMessage, NoteRevision,
    User, Patient, Encounter, Episode
)
from shared.events.publisher import publish_event, EventType

# Import schemas
from schemas import (
    VoiceSessionCreate, VoiceSessionResponse, VoiceSegmentCreate, VoiceSegmentResponse, FinalizeSessionRequest,
    CollabThreadCreate, CollabThreadUpdate, CollabThreadResponse, CollabThreadListResponse,
    CollabMessageCreate, CollabMessageResponse, CollabMessageListResponse,
    NoteRevisionCreate, NoteRevisionResponse, NoteRevisionListResponse, MarkFinalRequest
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
    title="Voice & Collaboration Service",
    description="Real-time voice transcription, multi-user collaboration, and note versioning",
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

def build_structured_transcript(segments: List[VoiceSegment]) -> dict:
    """Build structured transcript from segments with speaker diarization"""
    speakers = {}
    timeline = []

    for segment in sorted(segments, key=lambda s: s.segment_index):
        speaker_id = segment.speaker_id or "UNKNOWN"
        if speaker_id not in speakers:
            speakers[speaker_id] = {
                "speaker_id": speaker_id,
                "segments": [],
                "total_duration": 0.0
            }

        speakers[speaker_id]["segments"].append({
            "text": segment.text,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "confidence": segment.confidence
        })
        speakers[speaker_id]["total_duration"] += (segment.end_time - segment.start_time)

        timeline.append({
            "speaker": speaker_id,
            "text": segment.text,
            "start": segment.start_time,
            "end": segment.end_time
        })

    return {
        "speakers": speakers,
        "timeline": timeline,
        "total_speakers": len(speakers)
    }


def generate_note_from_voice(session: VoiceSession, template: Optional[str] = None) -> str:
    """
    Generate structured note from voice transcript

    In production, this would:
    - Use LLM to extract clinical entities
    - Format into SOAP/APSO structure
    - Apply note template
    - Ensure compliance with documentation guidelines

    For now, returns formatted transcript
    """
    if not session.transcript:
        return "# Progress Note\n\n_No transcript available_"

    note = f"# {session.session_type.replace('_', ' ').title()}\n\n"
    note += f"**Date:** {session.started_at.strftime('%Y-%m-%d %H:%M')}\n"
    note += f"**Duration:** {session.duration_seconds // 60} minutes\n\n"
    note += "---\n\n"
    note += "## Transcript\n\n"
    note += session.transcript

    # TODO: LLM-based structuring
    # In production: Extract S/O/A/P, medications, allergies, etc.

    return note


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-collab-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Voice Session Endpoints ====================

@app.post("/api/v1/voice/voice-sessions", response_model=VoiceSessionResponse, status_code=201)
async def create_voice_session(
    session_data: VoiceSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Start a new voice session for real-time transcription

    - Creates session with ASR configuration
    - Optionally enables speaker diarization
    - Links to encounter if provided
    - Publishes VOICE_SESSION_STARTED event
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == session_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate encounter if provided
        if session_data.encounter_id:
            encounter = db.query(Encounter).filter(Encounter.id == session_data.encounter_id).first()
            if not encounter:
                raise HTTPException(status_code=404, detail="Encounter not found")

        # Create voice session
        voice_session = VoiceSession(
            tenant_id=session_data.tenant_id,
            user_id=session_data.user_id,
            encounter_id=session_data.encounter_id,
            session_type=session_data.session_type,
            asr_model=session_data.asr_model,
            enable_diarization=session_data.enable_diarization,
            language=session_data.language,
            started_at=datetime.utcnow(),
            context=session_data.context,
            created_at=datetime.utcnow()
        )

        db.add(voice_session)
        db.commit()
        db.refresh(voice_session)

        # Publish event
        await publish_event(
            EventType.VOICE_SESSION_STARTED,
            {
                "session_id": str(voice_session.id),
                "tenant_id": str(voice_session.tenant_id),
                "user_id": str(voice_session.user_id),
                "session_type": voice_session.session_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Started voice session: {voice_session.id} for user {user.id}")
        return voice_session

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating voice session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/voice/voice-sessions/{session_id}", response_model=VoiceSessionResponse)
async def get_voice_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a voice session by ID

    - Returns session with full transcript
    - Includes structured transcript if diarization enabled
    """
    try:
        session = db.query(VoiceSession).filter(VoiceSession.id == session_id).first()

        if not session:
            raise HTTPException(status_code=404, detail="Voice session not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching voice session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/voice-sessions/{session_id}/segments", response_model=VoiceSegmentResponse, status_code=201)
async def ingest_voice_segment(
    session_id: UUID,
    segment_data: VoiceSegmentCreate,
    db: Session = Depends(get_db)
):
    """
    Ingest a transcript segment for a voice session

    - Real-time ASR sends segments as they're transcribed
    - Segments include speaker labels (if diarization enabled)
    - Word-level timestamps for precise alignment
    - Automatically updates session transcript
    """
    try:
        # Validate session exists
        session = db.query(VoiceSession).filter(VoiceSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Voice session not found")

        if session.ended_at:
            raise HTTPException(status_code=400, detail="Session already ended")

        # Create voice segment
        segment = VoiceSegment(
            voice_session_id=session_id,
            segment_index=segment_data.segment_index,
            start_time=segment_data.start_time,
            end_time=segment_data.end_time,
            text=segment_data.text,
            speaker_id=segment_data.speaker_id,
            confidence=segment_data.confidence,
            words=segment_data.words,
            created_at=datetime.utcnow()
        )

        db.add(segment)

        # Update session transcript (append new segment)
        if session.transcript:
            session.transcript += " " + segment_data.text
        else:
            session.transcript = segment_data.text

        db.commit()
        db.refresh(segment)

        logger.info(f"Ingested segment {segment_data.segment_index} for session {session_id}")
        return segment

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting voice segment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/voice-sessions/{session_id}/finalize", response_model=VoiceSessionResponse)
async def finalize_voice_session(
    session_id: UUID,
    finalize_request: FinalizeSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Finalize a voice session

    - Marks session as ended
    - Builds structured transcript with speaker diarization
    - Optionally generates structured note
    - Publishes VOICE_SESSION_ENDED event
    """
    try:
        # Get session
        session = db.query(VoiceSession).filter(VoiceSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Voice session not found")

        if session.ended_at:
            raise HTTPException(status_code=400, detail="Session already finalized")

        # Get all segments
        segments = db.query(VoiceSegment).filter(
            VoiceSegment.voice_session_id == session_id
        ).order_by(VoiceSegment.segment_index).all()

        # Build structured transcript
        if session.enable_diarization and segments:
            session.transcript_structured = build_structured_transcript(segments)

        # Calculate duration
        session.ended_at = datetime.utcnow()
        session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())

        db.commit()
        db.refresh(session)

        # Optionally generate note
        if finalize_request.generate_note and session.encounter_id:
            note_content = generate_note_from_voice(session, finalize_request.note_template)

            # Create note revision
            note = NoteRevision(
                tenant_id=session.tenant_id,
                encounter_id=session.encounter_id,
                note_type="progress_note",
                content=note_content,
                format="markdown",
                author_id=session.user_id,
                voice_session_id=session.id,
                ai_generated=True,
                ai_model="voice_transcript",
                revision_number=1,
                is_final=False,
                created_at=datetime.utcnow()
            )
            db.add(note)
            db.commit()

            logger.info(f"Generated note revision from voice session {session_id}")

        # Publish event
        await publish_event(
            EventType.VOICE_SESSION_ENDED,
            {
                "session_id": str(session.id),
                "tenant_id": str(session.tenant_id),
                "user_id": str(session.user_id),
                "duration_seconds": session.duration_seconds,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Finalized voice session: {session_id}")
        return session

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error finalizing voice session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Collaboration Thread Endpoints ====================

@app.post("/api/v1/collab/threads", response_model=CollabThreadResponse, status_code=201)
async def create_collaboration_thread(
    thread_data: CollabThreadCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new collaboration thread

    - Multi-user case discussions
    - MDRs, tumor boards, discharge planning
    - AI agents can participate
    - Mention tagging (@user, @role)
    - Publishes COLLAB_THREAD_CREATED event
    """
    try:
        # Validate creator exists
        creator = db.query(User).filter(User.id == thread_data.created_by).first()
        if not creator:
            raise HTTPException(status_code=404, detail="Creator user not found")

        # Create collaboration thread
        thread = CollabThread(
            tenant_id=thread_data.tenant_id,
            patient_id=thread_data.patient_id,
            encounter_id=thread_data.encounter_id,
            episode_id=thread_data.episode_id,
            title=thread_data.title,
            thread_type=thread_data.thread_type,
            description=thread_data.description,
            tags=thread_data.tags,
            participants=thread_data.participants,
            created_by=thread_data.created_by,
            status="active",
            message_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(thread)
        db.commit()
        db.refresh(thread)

        # Publish event
        await publish_event(
            EventType.COLLAB_THREAD_CREATED,
            {
                "thread_id": str(thread.id),
                "tenant_id": str(thread.tenant_id),
                "title": thread.title,
                "thread_type": thread.thread_type,
                "created_by": str(thread.created_by),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Created collaboration thread: {thread.title} (ID: {thread.id})")
        return thread

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating collaboration thread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/collab/threads", response_model=CollabThreadListResponse)
async def list_collaboration_threads(
    tenant_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    thread_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    participant_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List collaboration threads with filtering

    - Filter by patient, type, status, participant
    - Paginated results
    - Ordered by updated_at descending
    """
    try:
        # Build base query
        query = db.query(CollabThread)

        # Apply filters
        if tenant_id:
            query = query.filter(CollabThread.tenant_id == tenant_id)
        if patient_id:
            query = query.filter(CollabThread.patient_id == patient_id)
        if thread_type:
            query = query.filter(CollabThread.thread_type == thread_type.lower())
        if status:
            query = query.filter(CollabThread.status == status.lower())
        if participant_id:
            query = query.filter(CollabThread.participants.contains([participant_id]))

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        threads = query.order_by(desc(CollabThread.updated_at)).offset(offset).limit(page_size).all()

        return CollabThreadListResponse(
            total=total,
            threads=threads,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except Exception as e:
        logger.error(f"Error listing collaboration threads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/collab/threads/{thread_id}", response_model=CollabThreadResponse)
async def get_collaboration_thread(
    thread_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a collaboration thread by ID

    - Returns thread details with message count
    """
    try:
        thread = db.query(CollabThread).filter(CollabThread.id == thread_id).first()

        if not thread:
            raise HTTPException(status_code=404, detail="Collaboration thread not found")

        return thread

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching collaboration thread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/collab/threads/{thread_id}/messages", response_model=CollabMessageResponse, status_code=201)
async def post_message_to_thread(
    thread_id: UUID,
    message_data: CollabMessageCreate,
    db: Session = Depends(get_db)
):
    """
    Post a message to a collaboration thread

    - User messages, AI agent messages, system messages
    - Mention tagging (@user)
    - File attachments
    - Publishes COLLAB_MESSAGE_POSTED event
    """
    try:
        # Validate thread exists
        thread = db.query(CollabThread).filter(CollabThread.id == thread_id).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Collaboration thread not found")

        if thread.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot post to archived thread")

        # Validate author if user message
        if message_data.message_type == "user" and message_data.author_id:
            author = db.query(User).filter(User.id == message_data.author_id).first()
            if not author:
                raise HTTPException(status_code=404, detail="Author user not found")

        # Create message
        message = CollabMessage(
            collab_thread_id=thread_id,
            content=message_data.content,
            message_type=message_data.message_type,
            author_id=message_data.author_id,
            agent_name=message_data.agent_name,
            mentions=message_data.mentions,
            attachments=message_data.attachments,
            created_at=datetime.utcnow()
        )

        db.add(message)

        # Update thread message count and updated_at
        thread.message_count = (thread.message_count or 0) + 1
        thread.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)

        # Publish event
        await publish_event(
            EventType.COLLAB_MESSAGE_POSTED,
            {
                "message_id": str(message.id),
                "thread_id": str(thread_id),
                "tenant_id": str(thread.tenant_id),
                "message_type": message.message_type,
                "author_id": str(message.author_id) if message.author_id else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Posted message to thread {thread_id}")
        return message

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error posting message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/collab/threads/{thread_id}/messages", response_model=CollabMessageListResponse)
async def list_thread_messages(
    thread_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List messages in a collaboration thread

    - Returns messages in chronological order
    - Paginated results
    - Includes user and AI messages
    """
    try:
        # Validate thread exists
        thread = db.query(CollabThread).filter(CollabThread.id == thread_id).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Collaboration thread not found")

        # Build query
        query = db.query(CollabMessage).filter(CollabMessage.collab_thread_id == thread_id)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        messages = query.order_by(CollabMessage.created_at).offset(offset).limit(page_size).all()

        return CollabMessageListResponse(
            total=total,
            messages=messages,
            thread=thread,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing thread messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Note Revision Endpoints ====================

@app.post("/api/v1/collab/encounters/{encounter_id}/notes", response_model=NoteRevisionResponse, status_code=201)
async def create_note_revision(
    encounter_id: UUID,
    note_data: NoteRevisionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a note revision for an encounter

    - Versioned note editing
    - AI-generated or user-created
    - Can link to source voice session
    - Tracks revision history
    - Publishes NOTE_REVISION_CREATED event
    """
    try:
        # Validate encounter exists
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        # Validate author
        author = db.query(User).filter(User.id == note_data.author_id).first()
        if not author:
            raise HTTPException(status_code=404, detail="Author user not found")

        # Determine revision number
        existing_count = db.query(NoteRevision).filter(
            and_(
                NoteRevision.encounter_id == encounter_id,
                NoteRevision.note_type == note_data.note_type
            )
        ).count()
        revision_number = existing_count + 1

        # Create note revision
        note = NoteRevision(
            tenant_id=note_data.tenant_id,
            encounter_id=encounter_id,
            note_type=note_data.note_type,
            content=note_data.content,
            format=note_data.format,
            author_id=note_data.author_id,
            voice_session_id=note_data.voice_session_id,
            ai_generated=note_data.ai_generated,
            ai_model=note_data.ai_model,
            parent_revision_id=note_data.parent_revision_id,
            change_summary=note_data.change_summary,
            revision_number=revision_number,
            is_final=False,
            created_at=datetime.utcnow()
        )

        db.add(note)
        db.commit()
        db.refresh(note)

        # Publish event
        await publish_event(
            EventType.NOTE_REVISION_CREATED,
            {
                "revision_id": str(note.id),
                "encounter_id": str(encounter_id),
                "tenant_id": str(note.tenant_id),
                "note_type": note.note_type,
                "revision_number": note.revision_number,
                "ai_generated": note.ai_generated,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Created note revision {revision_number} for encounter {encounter_id}")
        return note

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Database integrity error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating note revision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/collab/encounters/{encounter_id}/notes", response_model=NoteRevisionListResponse)
async def list_note_revisions(
    encounter_id: UUID,
    note_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List note revisions for an encounter

    - Returns all revisions in chronological order
    - Can filter by note type
    - Shows revision history and edits
    """
    try:
        # Validate encounter exists
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        # Build query
        query = db.query(NoteRevision).filter(NoteRevision.encounter_id == encounter_id)

        # Filter by note type
        if note_type:
            query = query.filter(NoteRevision.note_type == note_type.lower())

        # Get total count
        total = query.count()

        # Apply pagination - newest first
        offset = (page - 1) * page_size
        revisions = query.order_by(desc(NoteRevision.created_at)).offset(offset).limit(page_size).all()

        return NoteRevisionListResponse(
            total=total,
            revisions=revisions,
            encounter_id=encounter_id,
            page=page,
            page_size=page_size,
            has_next=offset + page_size < total,
            has_previous=page > 1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing note revisions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/collab/note-revisions/{revision_id}/mark-final", response_model=NoteRevisionResponse)
async def mark_note_as_final(
    revision_id: UUID,
    finalize_request: MarkFinalRequest,
    db: Session = Depends(get_db)
):
    """
    Mark a note revision as final (signed/attested)

    - Once marked final, note becomes immutable
    - Records who attested and when
    - Creates permanent record for legal/compliance
    """
    try:
        # Get note revision
        note = db.query(NoteRevision).filter(NoteRevision.id == revision_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note revision not found")

        if note.is_final:
            raise HTTPException(status_code=400, detail="Note already marked as final")

        # Validate finalizing user
        finalizer = db.query(User).filter(User.id == finalize_request.finalized_by).first()
        if not finalizer:
            raise HTTPException(status_code=404, detail="Finalizing user not found")

        # Mark as final
        note.is_final = True
        note.finalized_at = datetime.utcnow()

        # Store attestation in change summary
        if finalize_request.attestation:
            note.change_summary = f"Finalized by {finalizer.id}: {finalize_request.attestation}"

        db.commit()
        db.refresh(note)

        logger.info(f"Marked note revision {revision_id} as final")
        return note

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking note as final: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8018)
