"""Schemas for LLM-native council generation."""
import json
import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class StepType(str, Enum):
    """Available step types for council workflows."""
    PARALLEL = "parallel"
    SEQUENCE = "sequence"
    DEBATE = "debate"
    SYNTHESIZE = "synthesize"
    SPLIT = "split"
    VOTE = "vote"
    REFINE = "refine"


class ModelChoice(str, Enum):
    """Available model choices."""
    CLAUDE_3_HAIKU = "claude-3-haiku"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_OPUS = "claude-3-opus"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo"


class AgentSpec(BaseModel):
    """Specification for a council agent."""
    
    id: str = Field(..., description="Unique identifier for the agent")
    prompt: str = Field(..., description="System prompt for the agent")
    model: str = Field(
        default=ModelChoice.CLAUDE_3_HAIKU,
        description="Model to use for this agent"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for model responses"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool names the agent can use"
    )
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model choice."""
        # Accept enum values
        if v in [m.value for m in ModelChoice]:
            return v
        # Also accept the enum directly
        if isinstance(v, ModelChoice):
            return v.value
        raise ValueError(f"Invalid model choice: {v}")


class StepSpec(BaseModel):
    """Specification for a workflow step."""
    
    type: StepType = Field(..., description="Type of step")
    agents: List[str] = Field(..., description="Agent IDs participating in this step")
    task_template: str = Field(
        default="{input}",
        description="Task template with placeholders"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific configuration"
    )


class CouncilSpec(BaseModel):
    """Complete specification for a council."""
    
    name: str = Field(..., description="Name of the council")
    description: Optional[str] = Field(None, description="Description of the council's purpose")
    agents: List[AgentSpec] = Field(..., description="List of agent specifications")
    steps: List[StepSpec] = Field(..., description="List of workflow steps")
    
    @model_validator(mode='after')
    def validate_agent_references(self) -> 'CouncilSpec':
        """Ensure all step agent references exist and agent IDs are unique."""
        # Check for duplicate agent IDs
        agent_ids = [agent.id for agent in self.agents]
        if len(agent_ids) != len(set(agent_ids)):
            duplicates = [id for id in agent_ids if agent_ids.count(id) > 1]
            raise ValueError(f"Duplicate agent IDs found: {duplicates}")
        
        # Check all step references exist
        for step in self.steps:
            for agent_id in step.agents:
                if agent_id not in agent_ids:
                    raise ValueError(
                        f"Step references undefined agent: {agent_id}. "
                        f"Available agents: {agent_ids}"
                    )
        
        return self


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response with multiple fallback strategies."""
    
    # Strategy 1: Direct parse
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Remove markdown formatting
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Find JSON object boundaries
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end+1])
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Use regex to extract valid JSON
    json_pattern = r'\{[^{}]*\}'
    matches = re.findall(json_pattern, cleaned, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # Strategy 5: More complex regex for nested JSON
    # This pattern handles nested objects better
    def find_json_objects(text: str) -> List[str]:
        """Find JSON objects in text, handling nesting."""
        objects = []
        depth = 0
        start = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    objects.append(text[start:i+1])
                    start = -1
        
        return objects
    
    json_objects = find_json_objects(cleaned)
    for obj in json_objects:
        try:
            return json.loads(obj)
        except json.JSONDecodeError:
            continue
    
    raise ValueError("No valid JSON found in response")