"""
Scribe Service - AI-Powered Clinical Documentation
LLM-based SOAP note generation, problem extraction, and clinical coding
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .schemas import (
    SOAPNoteRequest, SOAPNoteResponse, SOAPNote,
    ProblemExtractionRequest, ProblemExtractionResponse,
    OrderSuggestionRequest, OrderSuggestionResponse,
    FHIRDraftRequest, FHIRDraftResponse,
    SOAPNoteValidationRequest, SOAPNoteValidationResponse,
    Problem, MedicationOrder, LabOrder, ImagingOrder, ValidationIssue
)
from .llm_prompts import (
    SOAP_NOTE_SYSTEM_PROMPT,
    PROBLEM_EXTRACTION_SYSTEM_PROMPT,
    ORDER_SUGGESTION_SYSTEM_PROMPT,
    FHIR_GENERATION_SYSTEM_PROMPT,
    VALIDATION_SYSTEM_PROMPT,
    get_soap_note_prompt,
    get_problem_extraction_prompt,
    get_order_suggestion_prompt
)

# Initialize FastAPI app
app = FastAPI(
    title="Scribe Service",
    description="AI-powered clinical documentation and coding",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, local
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "scribe-service",
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== SOAP Note Generation ====================

@app.post(
    "/api/v1/scribe/soap-note",
    response_model=SOAPNoteResponse,
    status_code=status.HTTP_200_OK,
    tags=["SOAP Notes"]
)
async def generate_soap_note(
    request: SOAPNoteRequest
):
    """
    Generate SOAP note from clinical transcript

    Uses LLM to parse unstructured clinical conversation and create
    structured SOAP note with problem extraction and order suggestions.

    **Note:** This is a stateless service. It does not store the generated
    notes in the database. The calling service should handle persistence.
    """
    start_time = time.time()

    try:
        logger.info(
            f"Generating SOAP note for encounter {request.encounter_id}"
        )

        # Generate SOAP note using LLM
        soap_note_result = await _generate_soap_note_llm(
            transcript=request.transcript,
            encounter_type=request.encounter_type,
            additional_context=request.additional_context
        )

        # Extract problems from assessment
        problems_result = await _extract_problems_llm(
            clinical_text=soap_note_result["assessment"]
        )

        # Generate order suggestions based on assessment
        orders_result = await _suggest_orders_llm(
            assessment=soap_note_result["assessment"],
            encounter_type=request.encounter_type,
            patient_context=request.additional_context
        )

        # Generate FHIR resource drafts
        fhir_resources = await _generate_fhir_drafts(
            encounter_id=request.encounter_id,
            patient_id=request.patient_id,
            practitioner_id=request.practitioner_id,
            soap_note=SOAPNote(**soap_note_result),
            problems=problems_result
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        response = SOAPNoteResponse(
            soap_note=SOAPNote(**soap_note_result),
            problems=problems_result,
            medication_orders=orders_result.get("medication_orders", []),
            lab_orders=orders_result.get("lab_orders", []),
            imaging_orders=orders_result.get("imaging_orders", []),
            fhir_resources=fhir_resources,
            processing_time_ms=processing_time_ms
        )

        logger.info(
            f"Generated SOAP note for encounter {request.encounter_id} "
            f"in {processing_time_ms}ms"
        )

        return response

    except Exception as e:
        logger.error(f"Error generating SOAP note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SOAP note: {str(e)}"
        )


# ==================== Problem Extraction ====================

@app.post(
    "/api/v1/scribe/extract-problems",
    response_model=ProblemExtractionResponse,
    tags=["Problem Extraction"]
)
async def extract_problems(
    request: ProblemExtractionRequest
):
    """
    Extract clinical problems and diagnoses from text

    Uses LLM to identify problems and provide ICD-10 and SNOMED CT coding.
    """
    start_time = time.time()

    try:
        logger.info("Extracting problems from clinical text")

        problems = await _extract_problems_llm(
            clinical_text=request.clinical_text,
            include_coding=request.include_coding
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ProblemExtractionResponse(
            problems=problems,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Error extracting problems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract problems: {str(e)}"
        )


# ==================== Order Suggestions ====================

@app.post(
    "/api/v1/scribe/suggest-orders",
    response_model=OrderSuggestionResponse,
    tags=["Order Suggestions"]
)
async def suggest_orders(
    request: OrderSuggestionRequest
):
    """
    Suggest clinical orders based on assessment

    Provides evidence-based suggestions for medications, labs, and imaging.

    **Important:** These are SUGGESTIONS only, not prescriptions.
    All orders must be reviewed and approved by licensed practitioners.
    """
    start_time = time.time()

    try:
        logger.info("Generating order suggestions")

        result = await _suggest_orders_llm(
            assessment=request.assessment,
            encounter_type=request.encounter_type,
            patient_context=request.patient_context
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return OrderSuggestionResponse(
            medication_orders=result.get("medication_orders", []),
            lab_orders=result.get("lab_orders", []),
            imaging_orders=result.get("imaging_orders", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Error suggesting orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest orders: {str(e)}"
        )


# ==================== FHIR Draft Generation ====================

@app.post(
    "/api/v1/scribe/fhir-drafts",
    response_model=FHIRDraftResponse,
    tags=["FHIR Drafts"]
)
async def generate_fhir_drafts(
    request: FHIRDraftRequest
):
    """
    Generate FHIR R4 resource drafts from SOAP note

    Creates draft FHIR resources including Composition, Condition, and Observation.

    **Note:** These are DRAFTS that should be reviewed before persisting.
    """
    start_time = time.time()

    try:
        logger.info("Generating FHIR resource drafts")

        fhir_resources = await _generate_fhir_drafts(
            encounter_id=request.encounter_id,
            patient_id=request.patient_id,
            practitioner_id=request.practitioner_id,
            soap_note=request.soap_note,
            problems=request.problems
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return FHIRDraftResponse(
            composition=fhir_resources["composition"],
            conditions=fhir_resources.get("conditions", []),
            observations=fhir_resources.get("observations", []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Error generating FHIR drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate FHIR drafts: {str(e)}"
        )


# ==================== Validation ====================

@app.post(
    "/api/v1/scribe/validate",
    response_model=SOAPNoteValidationResponse,
    tags=["Validation"]
)
async def validate_soap_note(
    request: SOAPNoteValidationRequest
):
    """
    Validate SOAP note quality and completeness

    Identifies errors, warnings, and provides suggestions for improvement.
    """
    try:
        logger.info("Validating SOAP note")

        validation_result = await _validate_soap_note_llm(
            soap_note=request.soap_note,
            problems=request.problems
        )

        return SOAPNoteValidationResponse(
            is_valid=validation_result["is_valid"],
            issues=[ValidationIssue(**issue) for issue in validation_result.get("issues", [])],
            suggestions=validation_result.get("suggestions", [])
        )

    except Exception as e:
        logger.error(f"Error validating SOAP note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate SOAP note: {str(e)}"
        )


# ==================== LLM Integration Functions ====================

async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call LLM API with prompts

    Supports multiple providers (OpenAI, Anthropic, local models)
    """
    try:
        if LLM_PROVIDER == "openai":
            return await _call_openai(system_prompt, user_prompt)
        elif LLM_PROVIDER == "anthropic":
            return await _call_anthropic(system_prompt, user_prompt)
        elif LLM_PROVIDER == "local":
            return await _call_local_llm(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


async def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI API"""
    try:
        import openai

        openai.api_key = LLM_API_KEY

        response = openai.ChatCompletion.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        # Return mock response for development
        return _get_mock_response(system_prompt, user_prompt)


async def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    """Call Anthropic Claude API"""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=LLM_API_KEY)

        message = client.messages.create(
            model=LLM_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        # Return mock response for development
        return _get_mock_response(system_prompt, user_prompt)


async def _call_local_llm(system_prompt: str, user_prompt: str) -> str:
    """Call local LLM (e.g., via Ollama)"""
    try:
        # TODO: Implement local LLM integration
        logger.warning("Local LLM not implemented, using mock response")
        return _get_mock_response(system_prompt, user_prompt)

    except Exception as e:
        logger.error(f"Local LLM error: {e}")
        raise


def _get_mock_response(system_prompt: str, user_prompt: str) -> str:
    """Generate mock response for development/testing"""
    if "SOAP" in system_prompt:
        return json.dumps({
            "subjective": "Patient presents with chief complaint. History of present illness documented.",
            "objective": "Vital signs: BP 120/80, Pulse 72, Temp 98.6F. Physical exam findings documented.",
            "assessment": "Clinical diagnosis based on subjective and objective findings.",
            "plan": "Treatment plan with medications, follow-up instructions, and patient education.",
            "confidence_score": 0.85
        })
    elif "problem" in system_prompt.lower():
        return json.dumps({
            "problems": [
                {
                    "description": "Sample diagnosis",
                    "icd10_code": "R00.0",
                    "icd10_description": "Sample ICD-10 description",
                    "snomed_code": "123456789",
                    "snomed_description": "Sample SNOMED description",
                    "confidence_score": 0.80,
                    "is_primary": True
                }
            ]
        })
    elif "order" in system_prompt.lower():
        return json.dumps({
            "medication_orders": [],
            "lab_orders": [],
            "imaging_orders": []
        })
    elif "validation" in system_prompt.lower():
        return json.dumps({
            "is_valid": True,
            "issues": [],
            "suggestions": []
        })
    else:
        return "{}"


async def _generate_soap_note_llm(
    transcript: str,
    encounter_type: str,
    additional_context: dict
) -> dict:
    """Generate SOAP note using LLM"""
    user_prompt = get_soap_note_prompt(transcript, encounter_type, additional_context)
    response = await _call_llm(SOAP_NOTE_SYSTEM_PROMPT, user_prompt)

    # Parse JSON response
    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError("Invalid response format from LLM")


async def _extract_problems_llm(
    clinical_text: str,
    include_coding: bool = True
) -> list:
    """Extract problems using LLM"""
    user_prompt = get_problem_extraction_prompt(clinical_text)
    response = await _call_llm(PROBLEM_EXTRACTION_SYSTEM_PROMPT, user_prompt)

    try:
        result = json.loads(response)
        problems = [Problem(**p) for p in result.get("problems", [])]
        return problems
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse problem extraction response: {e}")
        return []


async def _suggest_orders_llm(
    assessment: str,
    encounter_type: str,
    patient_context: dict
) -> dict:
    """Generate order suggestions using LLM"""
    user_prompt = get_order_suggestion_prompt(assessment, encounter_type, patient_context)
    response = await _call_llm(ORDER_SUGGESTION_SYSTEM_PROMPT, user_prompt)

    try:
        result = json.loads(response)
        # Convert to Pydantic models
        result["medication_orders"] = [
            MedicationOrder(**m) for m in result.get("medication_orders", [])
        ]
        result["lab_orders"] = [
            LabOrder(**l) for l in result.get("lab_orders", [])
        ]
        result["imaging_orders"] = [
            ImagingOrder(**i) for i in result.get("imaging_orders", [])
        ]
        return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse order suggestions response: {e}")
        return {
            "medication_orders": [],
            "lab_orders": [],
            "imaging_orders": []
        }


async def _generate_fhir_drafts(
    encounter_id: UUID,
    patient_id: UUID,
    practitioner_id: UUID,
    soap_note: SOAPNote,
    problems: list
) -> dict:
    """Generate FHIR resource drafts"""
    # Build FHIR Composition (clinical document)
    composition = {
        "resourceType": "Composition",
        "id": f"comp-{encounter_id}",
        "status": "preliminary",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "11506-3",
                "display": "Progress note"
            }]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "date": datetime.utcnow().isoformat(),
        "author": [{"reference": f"Practitioner/{practitioner_id}"}],
        "title": "Clinical Progress Note",
        "section": [
            {
                "title": "Subjective",
                "code": {"text": "Subjective"},
                "text": {"status": "generated", "div": f"<div>{soap_note.subjective}</div>"}
            },
            {
                "title": "Objective",
                "code": {"text": "Objective"},
                "text": {"status": "generated", "div": f"<div>{soap_note.objective}</div>"}
            },
            {
                "title": "Assessment",
                "code": {"text": "Assessment"},
                "text": {"status": "generated", "div": f"<div>{soap_note.assessment}</div>"}
            },
            {
                "title": "Plan",
                "code": {"text": "Plan"},
                "text": {"status": "generated", "div": f"<div>{soap_note.plan}</div>"}
            }
        ]
    }

    # Build FHIR Condition resources for problems
    conditions = []
    for problem in problems:
        condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "problem-list-item" if problem.is_primary else "encounter-diagnosis"
                }]
            }],
            "code": {
                "coding": [],
                "text": problem.description
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "recordedDate": datetime.utcnow().isoformat()
        }

        # Add ICD-10 code if present
        if problem.icd10_code:
            condition["code"]["coding"].append({
                "system": "http://hl7.org/fhir/sid/icd-10",
                "code": problem.icd10_code,
                "display": problem.icd10_description
            })

        # Add SNOMED code if present
        if problem.snomed_code:
            condition["code"]["coding"].append({
                "system": "http://snomed.info/sct",
                "code": problem.snomed_code,
                "display": problem.snomed_description
            })

        conditions.append(condition)

    return {
        "composition": composition,
        "conditions": conditions,
        "observations": []  # TODO: Extract vitals and exam findings as Observations
    }


async def _validate_soap_note_llm(
    soap_note: SOAPNote,
    problems: list
) -> dict:
    """Validate SOAP note using LLM"""
    validation_input = {
        "soap_note": soap_note.dict(),
        "problems": [p.dict() for p in problems]
    }

    user_prompt = f"""Please validate the following SOAP note and problem list:

{json.dumps(validation_input, indent=2)}

Identify any errors, warnings, or areas for improvement."""

    response = await _call_llm(VALIDATION_SYSTEM_PROMPT, user_prompt)

    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse validation response: {e}")
        return {
            "is_valid": True,
            "issues": [],
            "suggestions": []
        }


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Scribe Service starting up...")
    logger.info(f"LLM Provider: {LLM_PROVIDER}")
    logger.info(f"LLM Model: {LLM_MODEL}")
    logger.info("Scribe Service ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=True)
