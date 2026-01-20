"""
Zoice Integration Router

Provides a transparent proxy gateway to the Zoice backend.
All requests to /admin/zoice/* are forwarded to the Zoice backend
with API key authentication.
"""

from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, Any, Dict
import logging

from .client import get_zoice_client, ZoiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/zoice", tags=["Zoice Integration (Admin)"])


def get_client() -> ZoiceClient:
    """Dependency to get the Zoice client."""
    try:
        return get_zoice_client()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Zoice integration not configured. Please set ZOICE_BASE_URL and ZOICE_API_KEY."
        )


# =============================================================================
# TRANSPARENT PROXY ENDPOINT
# =============================================================================

@router.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="Transparent proxy to Zoice backend"
)
async def proxy_to_zoice(
    request: Request,
    path: str,
    client: ZoiceClient = Depends(get_client)
):
    """
    Transparently proxy requests to the Zoice backend.

    This endpoint forwards all requests to the corresponding Zoice API endpoint,
    preserving the method, query parameters, and request body.

    Examples:
    - GET /admin/zoice/proxy/pipelines/list -> GET /pipelines/list on Zoice
    - POST /admin/zoice/proxy/pipelines/create -> POST /pipelines/create on Zoice
    """
    # Get query params
    params = dict(request.query_params) if request.query_params else None

    # Get request body for non-GET requests
    json_body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            json_body = await request.json()
        except Exception:
            json_body = None

    # Forward to Zoice
    response = await client.proxy_request(
        method=request.method,
        path=f"/{path}",
        params=params,
        json_body=json_body
    )

    # Return the response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type", "application/json")
    )


# =============================================================================
# TYPED ENDPOINTS (For better documentation and type safety)
# =============================================================================

# --- Pipelines ---

@router.get("/pipelines", summary="List all pipelines")
async def list_pipelines(
    pipeline_type: Optional[str] = Query(None, description="Filter by pipeline type: 'realtime' or 'turn_based'"),
    client: ZoiceClient = Depends(get_client)
):
    """Get list of all pipelines from Zoice."""
    return await client.get_pipelines(pipeline_type=pipeline_type)


@router.get("/pipelines/{pipeline_id}", summary="Get pipeline by ID")
async def get_pipeline(
    pipeline_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Get a specific pipeline by its ID."""
    return await client.get_pipeline(pipeline_id)


@router.post("/pipelines", summary="Create a new pipeline")
async def create_pipeline(
    request: Request,
    agent_template_id: Optional[str] = Query(None, description="Agent template ID to clone from"),
    client: ZoiceClient = Depends(get_client)
):
    """Create a new pipeline in Zoice."""
    data = await request.json()
    return await client.create_pipeline(data, agent_template_id=agent_template_id)


@router.put("/pipelines/{pipeline_id}", summary="Update a pipeline")
async def update_pipeline(
    pipeline_id: str,
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Update an existing pipeline."""
    data = await request.json()
    return await client.update_pipeline(pipeline_id, data)


@router.delete("/pipelines/{pipeline_id}", summary="Delete a pipeline")
async def delete_pipeline(
    pipeline_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Soft delete a pipeline."""
    return await client.delete_pipeline(pipeline_id)


# --- Pipeline Analytics ---

@router.get("/pipelines/{pipeline_id}/analytics", summary="Get pipeline analytics")
async def get_pipeline_analytics(
    pipeline_id: str,
    period: Optional[str] = Query(None, description="Options: last_7_days, last_30_days"),
    client: ZoiceClient = Depends(get_client)
):
    """Get analytics for a specific pipeline."""
    params = {"period": period} if period else None
    response = await client.proxy_request("GET", f"/pipelines/analytics/{pipeline_id}", params=params)
    response.raise_for_status()
    return response.json()


# --- Pipeline Phone Numbers ---

@router.get("/pipelines/{pipeline_id}/phone-numbers", summary="Get phone numbers assigned to pipeline")
async def get_pipeline_phone_numbers(
    pipeline_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Get phone numbers assigned to a pipeline."""
    response = await client.proxy_request("GET", f"/pipelines/{pipeline_id}/phone-numbers")
    response.raise_for_status()
    return response.json()


@router.post("/pipelines/{pipeline_id}/assign-phone-numbers", summary="Assign phone numbers to pipeline")
async def assign_phone_numbers_to_pipeline(
    pipeline_id: str,
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Assign phone numbers to a pipeline for incoming calls."""
    data = await request.json()
    response = await client.proxy_request("POST", f"/pipelines/{pipeline_id}/assign-phone-numbers", json_body=data)
    response.raise_for_status()
    return response.json()


# --- Agents ---

@router.get("/agents", summary="List all agents")
async def list_agents(client: ZoiceClient = Depends(get_client)):
    """Get list of all agents."""
    return await client.get_agents()


@router.get("/agents/templates", summary="List agent templates")
async def list_agent_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    client: ZoiceClient = Depends(get_client)
):
    """Get paginated list of agent templates."""
    return await client.get_agent_templates(page=page, page_size=page_size)


@router.get("/agents/{agent_id}", summary="Get agent by ID")
async def get_agent(
    agent_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Get a specific agent by ID."""
    response = await client.proxy_request("GET", f"/agents/get/{agent_id}")
    response.raise_for_status()
    return response.json()


@router.post("/agents", summary="Create a new agent")
async def create_agent(
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Create a new agent."""
    data = await request.json()
    response = await client.proxy_request("POST", "/agents/create", json_body=data)
    response.raise_for_status()
    return response.json()


@router.put("/agents/{agent_id}", summary="Update an agent")
async def update_agent(
    agent_id: str,
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Update an agent."""
    data = await request.json()
    response = await client.proxy_request("PUT", f"/agents/update/{agent_id}", json_body=data)
    response.raise_for_status()
    return response.json()


@router.delete("/agents/{agent_id}", summary="Delete an agent")
async def delete_agent(
    agent_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Delete an agent."""
    response = await client.proxy_request("DELETE", f"/agents/delete/{agent_id}")
    response.raise_for_status()
    return response.json()


# --- Calls ---

@router.get("/calls", summary="List calls")
async def list_calls(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    client: ZoiceClient = Depends(get_client)
):
    """Get paginated list of calls."""
    return await client.get_calls(page=page, limit=limit)


@router.get("/calls/{call_id}", summary="Get call by ID")
async def get_call(
    call_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Get a specific call by ID."""
    response = await client.proxy_request("GET", f"/calls/get/{call_id}")
    response.raise_for_status()
    return response.json()


@router.post("/calls", summary="Create/schedule a call")
async def create_call(
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Schedule a new outbound call."""
    data = await request.json()
    response = await client.proxy_request("POST", "/calls/create", json_body=data)
    response.raise_for_status()
    return response.json()


@router.post("/calls/aggregate", summary="Get call statistics")
async def aggregate_calls(
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Aggregate call statistics over a time period."""
    data = await request.json()
    response = await client.proxy_request("POST", "/calls/aggregate", json_body=data)
    response.raise_for_status()
    return response.json()


# --- Phone Numbers ---

@router.get("/phone-numbers/available", summary="Get available phone numbers")
async def get_available_phone_numbers(client: ZoiceClient = Depends(get_client)):
    """Get phone numbers not yet assigned to a pipeline."""
    return await client.get_phone_numbers_available()


@router.get("/telephony-configs", summary="List telephony configurations")
async def list_telephony_configs(client: ZoiceClient = Depends(get_client)):
    """Get all telephony configurations."""
    response = await client.proxy_request("GET", "/telephony-configs/list")
    response.raise_for_status()
    return response.json()


# --- Provider Configurations (STT, TTS, LLM, VAD) ---

@router.get("/provider-configurations", summary="List provider configurations")
async def list_provider_configurations(
    service_type: Optional[str] = Query(None, description="Filter by type: stt, tts, llm, vad, realtime_audio"),
    client: ZoiceClient = Depends(get_client)
):
    """Get provider configurations."""
    params = {"service_type": service_type} if service_type else None
    response = await client.proxy_request("GET", "/provider-configurations/list", params=params)
    response.raise_for_status()
    return response.json()


@router.get("/provider-configurations/library", summary="Get provider library")
async def get_provider_library(
    service_type: Optional[str] = Query(None, description="Filter by type: stt, tts, llm, vad, realtime_audio"),
    client: ZoiceClient = Depends(get_client)
):
    """Get default provider configurations library."""
    params = {"service_type": service_type} if service_type else None
    response = await client.proxy_request("GET", "/provider-configurations/library", params=params)
    response.raise_for_status()
    return response.json()


@router.post("/provider-configurations", summary="Create provider configuration")
async def create_provider_configuration(
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Create a new provider configuration."""
    data = await request.json()
    response = await client.proxy_request("POST", "/provider-configurations/create", json_body=data)
    response.raise_for_status()
    return response.json()


# --- Extraction Prompts ---

@router.get("/extraction-prompts/{prompt_id}", summary="Get extraction prompt")
async def get_extraction_prompt(
    prompt_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Get an extraction prompt by ID."""
    response = await client.proxy_request("GET", f"/extraction-prompt/get/{prompt_id}")
    response.raise_for_status()
    return response.json()


@router.post("/extraction-prompts", summary="Create extraction prompt")
async def create_extraction_prompt(
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Create a new extraction prompt."""
    data = await request.json()
    response = await client.proxy_request("POST", "/extraction-prompt/create", json_body=data)
    response.raise_for_status()
    return response.json()


@router.put("/extraction-prompts/{prompt_id}", summary="Update extraction prompt")
async def update_extraction_prompt(
    prompt_id: str,
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Update an extraction prompt."""
    data = await request.json()
    response = await client.proxy_request("PUT", f"/extraction-prompt/update/{prompt_id}", json_body=data)
    response.raise_for_status()
    return response.json()


# --- Webhooks ---

@router.get("/webhooks", summary="List webhooks")
async def list_webhooks(client: ZoiceClient = Depends(get_client)):
    """Get all configured webhooks."""
    response = await client.proxy_request("GET", "/webhooks/list")
    response.raise_for_status()
    return response.json()


@router.post("/webhooks", summary="Create webhook")
async def create_webhook(
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Create a new webhook configuration."""
    data = await request.json()
    response = await client.proxy_request("POST", "/webhooks/create", json_body=data)
    response.raise_for_status()
    return response.json()


@router.put("/webhooks/{webhook_id}", summary="Update webhook")
async def update_webhook(
    webhook_id: str,
    request: Request,
    client: ZoiceClient = Depends(get_client)
):
    """Update a webhook configuration."""
    data = await request.json()
    response = await client.proxy_request("PUT", f"/webhooks/update/{webhook_id}", json_body=data)
    response.raise_for_status()
    return response.json()


@router.delete("/webhooks/{webhook_id}", summary="Delete webhook")
async def delete_webhook(
    webhook_id: str,
    client: ZoiceClient = Depends(get_client)
):
    """Delete a webhook configuration."""
    response = await client.proxy_request("DELETE", f"/webhooks/delete/{webhook_id}")
    response.raise_for_status()
    return response.json()


# --- Reference Data (Industries, Use Cases, Languages, Voices) ---

@router.get("/industries", summary="List industries")
async def list_industries(client: ZoiceClient = Depends(get_client)):
    """Get list of industries."""
    response = await client.proxy_request("GET", "/agents/v1/industry/list")
    response.raise_for_status()
    return response.json()


@router.get("/use-cases", summary="List use cases")
async def list_use_cases(
    industry_id: Optional[str] = Query(None, description="Filter by industry ID"),
    client: ZoiceClient = Depends(get_client)
):
    """Get list of use cases."""
    params = {"industry_id": industry_id} if industry_id else None
    response = await client.proxy_request("GET", "/agents/v1/use-case/list", params=params)
    response.raise_for_status()
    return response.json()


@router.get("/languages", summary="List languages")
async def list_languages(client: ZoiceClient = Depends(get_client)):
    """Get list of supported languages."""
    response = await client.proxy_request("GET", "/agents/v1/language/list")
    response.raise_for_status()
    return response.json()


@router.get("/voices", summary="List voices")
async def list_voices(
    language_ids: Optional[str] = Query(None, description="Comma-separated language IDs"),
    client: ZoiceClient = Depends(get_client)
):
    """Get list of available voices."""
    params = {"language_ids": language_ids} if language_ids else None
    response = await client.proxy_request("GET", "/agents/v1/voice/list", params=params)
    response.raise_for_status()
    return response.json()


@router.get("/llms", summary="List LLMs")
async def list_llms(client: ZoiceClient = Depends(get_client)):
    """Get list of available LLM configurations."""
    response = await client.proxy_request("GET", "/agents/v1/llm/list")
    response.raise_for_status()
    return response.json()


@router.get("/stts", summary="List STT providers")
async def list_stts(client: ZoiceClient = Depends(get_client)):
    """Get list of available STT (Speech-to-Text) configurations."""
    response = await client.proxy_request("GET", "/agents/v1/stt/list")
    response.raise_for_status()
    return response.json()


# --- Health Check ---

@router.get("/health", summary="Zoice connection health check")
async def health_check(client: ZoiceClient = Depends(get_client)):
    """Check if the Zoice backend is reachable."""
    try:
        response = await client.proxy_request("GET", "/health")
        return {
            "status": "connected",
            "zoice_status": response.status_code,
            "zoice_healthy": response.status_code == 200
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
