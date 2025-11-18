"""
Agents Module Schemas
Schemas for AI agent tool execution
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ==================== Tool Registry ====================

class ToolDefinition(BaseModel):
    """Definition of an available tool"""
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="What the tool does")
    inputs: Dict[str, str] = Field(..., description="Input schema {param_name: type}")
    scopes: List[str] = Field(default_factory=list, description="Required permissions")


class ToolRegistry(BaseModel):
    """List of available tools"""
    tools: List[ToolDefinition]


# ==================== Tool Execution ====================

class RunTool(BaseModel):
    """Execute a tool"""
    name: str = Field(..., min_length=1, max_length=64, description="Tool to execute")
    args: Dict[str, Any] = Field(..., description="Tool arguments")


class ToolRunResponse(BaseModel):
    """Result of tool execution"""
    id: UUID
    org_id: UUID
    tool: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    success: bool
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Tool Run History ====================

class ToolRunListFilters(BaseModel):
    """Filters for listing tool runs"""
    tool: Optional[str] = None
    success: Optional[bool] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ToolRunStatistics(BaseModel):
    """Statistics about tool executions"""
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float = Field(..., ge=0.0, le=1.0)
    by_tool: Dict[str, int] = Field(..., description="Runs per tool")
    most_used_tool: Optional[str]
    most_failed_tool: Optional[str]
