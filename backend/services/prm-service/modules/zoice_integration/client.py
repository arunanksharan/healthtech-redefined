"""
Zoice API Client

Provides an async HTTP client for communicating with the Zoice backend
using API key authentication.
"""

import httpx
from typing import Optional, Any, Dict
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class ZoiceClient:
    """
    Async HTTP client for Zoice API.

    Uses API key authentication via X-API-Key header.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        """
        Initialize the Zoice client.

        Args:
            base_url: Zoice backend base URL (e.g., "http://localhost:8000")
            api_key: Zoice API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> Dict[str, str]:
        """Default headers for all requests."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def proxy_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Proxy a request to the Zoice backend.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API path (e.g., "/pipelines/list")
            params: Query parameters
            json_body: JSON request body
            data: Form data
            files: File uploads

        Returns:
            httpx.Response from Zoice backend

        Raises:
            HTTPException: If the request fails
        """
        client = await self._get_client()

        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"

        logger.info(f"Proxying {method} request to Zoice: {path}")

        try:
            # Build request kwargs
            kwargs: Dict[str, Any] = {}
            if params:
                kwargs["params"] = params
            if json_body:
                kwargs["json"] = json_body
            elif data:
                kwargs["data"] = data
            if files:
                kwargs["files"] = files
                # Remove content-type header for multipart
                if "json" not in kwargs:
                    del kwargs.get("headers", {}).get("Content-Type", None)

            response = await client.request(method, path, **kwargs)

            logger.info(f"Zoice response: {response.status_code}")
            return response

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Zoice: {path}")
            raise HTTPException(
                status_code=504,
                detail="Zoice service timeout"
            )
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Zoice: {path}")
            raise HTTPException(
                status_code=503,
                detail="Zoice service unavailable"
            )
        except Exception as e:
            logger.error(f"Error proxying to Zoice: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Error communicating with Zoice: {str(e)}"
            )

    # Convenience methods for specific endpoints

    async def get_pipelines(self, pipeline_type: Optional[str] = None) -> Dict[str, Any]:
        """Get list of pipelines."""
        params = {}
        if pipeline_type:
            params["pipeline_type"] = pipeline_type
        response = await self.proxy_request("GET", "/pipelines/list", params=params)
        response.raise_for_status()
        return response.json()

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Get a specific pipeline."""
        response = await self.proxy_request("GET", f"/pipelines/get/{pipeline_id}")
        response.raise_for_status()
        return response.json()

    async def create_pipeline(self, data: Dict[str, Any], agent_template_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new pipeline."""
        params = {}
        if agent_template_id:
            params["agent_template_id"] = agent_template_id
        response = await self.proxy_request("POST", "/pipelines/create", params=params, json_body=data)
        response.raise_for_status()
        return response.json()

    async def update_pipeline(self, pipeline_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a pipeline."""
        response = await self.proxy_request("PUT", f"/pipelines/update/{pipeline_id}", json_body=data)
        response.raise_for_status()
        return response.json()

    async def delete_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline."""
        response = await self.proxy_request("DELETE", f"/pipelines/delete/{pipeline_id}")
        response.raise_for_status()
        return response.json()

    async def get_agents(self) -> Dict[str, Any]:
        """Get list of agents."""
        response = await self.proxy_request("GET", "/agents/list")
        response.raise_for_status()
        return response.json()

    async def get_agent_templates(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get agent templates."""
        response = await self.proxy_request(
            "GET",
            "/agents/v1/template/list/",
            params={"page": page, "page_size": page_size}
        )
        response.raise_for_status()
        return response.json()

    async def get_calls(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get list of calls."""
        response = await self.proxy_request(
            "GET",
            "/calls/list",
            params={"page": page, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def get_phone_numbers_available(self) -> Dict[str, Any]:
        """Get available phone numbers."""
        response = await self.proxy_request("GET", "/telephony-configs/phone-numbers/available")
        response.raise_for_status()
        return response.json()


# Global client instance (initialized on startup)
_zoice_client: Optional[ZoiceClient] = None


def get_zoice_client() -> ZoiceClient:
    """Get the global Zoice client instance."""
    if _zoice_client is None:
        raise RuntimeError("Zoice client not initialized. Call init_zoice_client() first.")
    return _zoice_client


def init_zoice_client(base_url: str, api_key: str) -> ZoiceClient:
    """Initialize the global Zoice client."""
    global _zoice_client
    _zoice_client = ZoiceClient(base_url=base_url, api_key=api_key)
    logger.info(f"Zoice client initialized with base URL: {base_url}")
    return _zoice_client


async def close_zoice_client():
    """Close the global Zoice client."""
    global _zoice_client
    if _zoice_client:
        await _zoice_client.close()
        _zoice_client = None
        logger.info("Zoice client closed")
