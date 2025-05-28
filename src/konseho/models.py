"""Pydantic models for Konseho data structures."""
from __future__ import annotations

from typing import Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from konseho.protocols import JSON, AgentCapabilities, StepMetadata, SearchResult, ToolResult


class HistoryEntry(BaseModel):
    """Agent history entry."""
    task: str
    response: str


class StepConfig(BaseModel):
    """Configuration for a step."""
    model_config = ConfigDict(extra='forbid')
    
    description: str
    task_template: Optional[str] = None
    rounds: Optional[int] = None
    moderator_index: Optional[int] = None
    max_splits: Optional[int] = None


class StepTemplate(BaseModel):
    """Template for creating a step."""
    model_config = ConfigDict(extra='forbid')
    
    type: str  # Will be class name
    config: StepConfig


class TaskAnalysis(BaseModel):
    """Analysis result from task analyzer."""
    model_config = ConfigDict(extra='forbid')
    
    task_type: str  # TaskType enum value
    complexity: str
    needs_parallel: bool
    needs_debate: bool
    query: str
    domains: list[str]


class ServerInfo(BaseModel):
    """Information about an MCP server."""
    model_config = ConfigDict(extra='forbid')
    
    name: str
    enabled: bool
    running: bool
    command: str
    tools: int


class CouncilResult(BaseModel):
    """Result from council execution."""
    model_config = ConfigDict(extra='forbid')
    
    council: str
    task: str
    workflow: str
    steps_completed: int
    agents_involved: list[str]
    summary: Optional[str] = None
    final_output: Optional[str] = None
    metadata: dict[str, JSON] = Field(default_factory=dict)


class StepResultData(BaseModel):
    """Data structure for step results."""
    model_config = ConfigDict(extra='forbid')
    
    output: str
    metadata: dict[str, JSON] = Field(default_factory=dict)
    success: bool = True


class EventData(BaseModel):
    """Data for events emitted during execution."""
    model_config = ConfigDict(extra='allow')
    
    event_type: str
    timestamp: str
    data: dict[str, JSON] = Field(default_factory=dict)