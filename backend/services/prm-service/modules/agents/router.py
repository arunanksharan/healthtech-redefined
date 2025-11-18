"""
Agents Router
API endpoints for AI agent tool execution
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from loguru import logger

from shared.database.connection import get_db

from modules.agents.schemas import (
    ToolRegistry,
    RunTool,
    ToolRunResponse,
    ToolRunListFilters,
    ToolRunStatistics
)
from modules.agents.service import AgentService


router = APIRouter(prefix="/agents", tags=["AI Agents"])


# ==================== Tool Registry ====================

@router.get("/tools", response_model=ToolRegistry)
async def list_tools():
    """
    List all available tools for AI agents

    Returns registry of tools that can be executed including:
      - Tool name
      - Description
      - Input schema
      - Required permissions

    Available tools:
      - create_ticket: Create support ticket
      - confirm_appointment: Confirm appointment with time
      - send_notification: Send WhatsApp/SMS/Email
      - update_patient: Update patient information

    Use case:
      - AI agent retrieves tool list
      - Agent selects appropriate tool based on user request
      - Agent calls /agents/run with tool name and args
    """
    service = AgentService(None)  # No DB needed for tool registry
    return service.list_tools()


# ==================== Tool Execution ====================

@router.post("/run", response_model=dict)
async def run_tool(
    payload: RunTool,
    db: Session = Depends(get_db)
):
    """
    Execute a tool

    Process:
      1. Validates tool exists
      2. Creates ToolRun log entry
      3. Executes tool via appropriate handler
      4. Updates log with result
      5. Returns tool output

    Example request:
    ```json
    {
      "name": "create_ticket",
      "args": {
        "category": "technical",
        "priority": "high",
        "summary": "Patient unable to book appointment",
        "description": "Error when clicking Book button"
      }
    }
    ```

    Example response:
    ```json
    {
      "ticket_id": "uuid",
      "status": "open"
    }
    ```

    All executions are logged in ToolRun table for:
      - Audit trail
      - Debugging
      - Analytics
    """
    service = AgentService(db)

    try:
        # TODO: Get org_id from auth context
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        output = await service.execute_tool(org_id, payload)
        return output

    except ValueError as e:
        logger.warning(f"Invalid tool request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


# ==================== Tool Run History ====================

@router.get("/runs", response_model=List[ToolRunResponse])
async def list_tool_runs(
    tool: str = None,
    success: bool = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List tool run history

    Query parameters:
      - tool: Filter by tool name
      - success: Filter by success/failure
      - limit: Number of results (1-100, default 50)
      - offset: Skip N results

    Returns list of tool runs sorted by most recent first.

    Use cases:
      - Audit trail: Review all tool executions
      - Debugging: Find failed tool runs
      - Analytics: Analyze tool usage patterns
    """
    service = AgentService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        filters = ToolRunListFilters(
            tool=tool,
            success=success,
            limit=limit,
            offset=offset
        )

        runs = await service.list_tool_runs(org_id, filters)

        return [ToolRunResponse.from_orm(run) for run in runs]

    except Exception as e:
        logger.error(f"Error listing tool runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tool runs: {str(e)}")


@router.get("/runs/{tool_run_id}", response_model=ToolRunResponse)
async def get_tool_run(
    tool_run_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get tool run details

    Returns:
      - Tool name
      - Input arguments
      - Output (if successful)
      - Error message (if failed)
      - Timestamps
    """
    service = AgentService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        run = await service.get_tool_run(org_id, tool_run_id)

        if not run:
            raise HTTPException(status_code=404, detail="Tool run not found")

        return ToolRunResponse.from_orm(run)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get tool run: {str(e)}")


# ==================== Statistics ====================

@router.get("/stats", response_model=ToolRunStatistics)
async def get_statistics(
    db: Session = Depends(get_db)
):
    """
    Get tool execution statistics

    Returns:
      - Total runs
      - Successful/failed counts
      - Success rate
      - Runs per tool
      - Most used tool
      - Most failed tool

    Use cases:
      - Monitor agent performance
      - Identify problematic tools
      - Usage analytics
    """
    service = AgentService(db)

    try:
        org_id = UUID("a87e6e1e-c028-4e7c-a06c-12cf5a3c133a")

        stats = await service.get_statistics(org_id)
        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ==================== Health Check ====================

@router.get("/health/check")
async def agents_health_check():
    """Health check for agents module"""
    service = AgentService(None)
    tools = service.list_tools()

    return {
        "status": "healthy",
        "module": "agents",
        "features": [
            "tool_execution",
            "execution_logging",
            "audit_trail"
        ],
        "available_tools": len(tools.tools),
        "tools": [tool.name for tool in tools.tools]
    }
