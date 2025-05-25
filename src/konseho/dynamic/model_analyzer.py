"""Model-based query analyzer using LLM for sophisticated analysis."""

import json
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum

from ..agents.base import create_agent
from .analyzer import TaskType


ANALYZER_PROMPT = """You are a query analyzer for a multi-agent council system. Your job is to analyze user queries and determine the optimal configuration for a council of AI agents to solve the task.

{persona_registry}

IMPORTANT: You MUST only use agents from the available personas listed above. Do not create new agent names.

Analyze the given query and return a JSON object with the following structure:

{
    "task_type": "research|code_review|design|analysis|planning|debate|implementation|general",
    "domains": ["technical", "business", "creative", "scientific"],  // List relevant domains
    "complexity": "low|medium|high",
    "suggested_agents": [
        {
            "name": "Agent Name",
            "role": "Brief description of agent's role",
            "expertise": "Specific expertise area",
            "personality": "collaborative|analytical|creative|critical|pragmatic"
        }
    ],
    "workflow_steps": [
        {
            "type": "debate|parallel|split",
            "description": "What happens in this step",
            "participants": ["Agent Name 1", "Agent Name 2"]  // Which agents participate
        }
    ],
    "reasoning": "Brief explanation of why this configuration was chosen"
}

Guidelines:
1. For task_type, choose the most appropriate category based on the primary goal
2. Include 2-6 agents depending on complexity (more complex = more agents)
3. Each agent should have a distinct role and expertise
4. Workflow should have 1-3 steps maximum
5. Use "parallel" steps when agents can work independently on different aspects
6. Use "debate" steps when different perspectives need to be reconciled
7. Use "split" steps when the same type of work needs to be distributed

Examples:

Query: "Review this Python code for security vulnerabilities"
{
    "task_type": "code_review",
    "domains": ["technical"],
    "complexity": "medium",
    "suggested_agents": [
        {"name": "Security Expert", "role": "Identify security vulnerabilities", "expertise": "security", "personality": "critical"},
        {"name": "Code Architect", "role": "Review overall design", "expertise": "architecture", "personality": "analytical"},
        {"name": "Best Practices Auditor", "role": "Check coding standards", "expertise": "quality", "personality": "pragmatic"}
    ],
    "workflow_steps": [
        {"type": "parallel", "description": "Initial independent review", "participants": ["Security Expert", "Code Architect", "Best Practices Auditor"]},
        {"type": "debate", "description": "Discuss findings and prioritize issues", "participants": ["Security Expert", "Code Architect", "Best Practices Auditor"]}
    ],
    "reasoning": "Code review benefits from multiple specialized perspectives working in parallel, followed by discussion to prioritize findings."
}

Query: "Design a scalable e-commerce platform"
{
    "task_type": "design",
    "domains": ["technical", "business"],
    "complexity": "high",
    "suggested_agents": [
        {"name": "Solutions Architect", "role": "Design system architecture", "expertise": "architecture", "personality": "analytical"},
        {"name": "Business Analyst", "role": "Define business requirements", "expertise": "business", "personality": "pragmatic"},
        {"name": "UX Designer", "role": "Design user experience", "expertise": "design", "personality": "creative"},
        {"name": "Tech Lead", "role": "Evaluate technical feasibility", "expertise": "implementation", "personality": "pragmatic"},
        {"name": "Scalability Expert", "role": "Ensure system can scale", "expertise": "performance", "personality": "analytical"}
    ],
    "workflow_steps": [
        {"type": "debate", "description": "Initial brainstorming and requirements", "participants": ["Solutions Architect", "Business Analyst", "UX Designer", "Tech Lead", "Scalability Expert"]},
        {"type": "parallel", "description": "Detailed design of components", "participants": ["Solutions Architect", "UX Designer", "Scalability Expert"]},
        {"type": "debate", "description": "Final review and integration", "participants": ["Solutions Architect", "Business Analyst", "UX Designer", "Tech Lead", "Scalability Expert"]}
    ],
    "reasoning": "Complex design task requires diverse expertise. Start with collaborative brainstorming, then parallel detailed work, ending with integration discussion."
}

Now analyze the following query and return ONLY the JSON response, no additional text:
"""


class ModelBasedAnalyzer:
    """Uses an LLM to analyze queries and suggest council configurations."""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0.3):
        """Initialize the analyzer.
        
        Args:
            model: Model to use for analysis (defaults to config if not specified)
            temperature: Temperature for analysis (lower = more consistent)
        """
        self.model = model
        self.temperature = temperature
        
        # Get persona registry and inject into prompt
        from .persona_registry import PERSONA_REGISTRY
        self.registry = PERSONA_REGISTRY
        prompt_with_registry = ANALYZER_PROMPT.replace(
            "{persona_registry}", 
            self.registry.get_registry_summary()
        )
        
        self._analyzer_agent = create_agent(
            name="QueryAnalyzer",
            system_prompt=prompt_with_registry,
            temperature=temperature,
            model=model  # Pass the model parameter to create_agent
        )
    
    async def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze a query using the LLM.
        
        Args:
            query: The user's query to analyze
            
        Returns:
            Analysis results with task type, agents, and workflow
        """
        try:
            # Get analysis from model
            # Call the agent directly in executor since Strands agents are synchronous
            loop = asyncio.get_event_loop()
            agent_result = await loop.run_in_executor(None, self._analyzer_agent, query)
            
            # Extract the message from the result
            json_str = None
            analysis = None
            
            # Convert result to string to get the actual content
            result_str = str(agent_result)
            
            # The result string should contain the JSON
            if result_str:
                json_str = result_str.strip()
            
            # Parse JSON response if we have a string response
            if json_str is not None and analysis is None:
                # The response might have markdown formatting, so extract JSON
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                
                analysis = json.loads(json_str.strip())
            
            # Ensure we have analysis
            if analysis is None:
                raise ValueError("Failed to extract analysis from model response")
            
            # Debug: check what we have
            #print(f"DEBUG: Analysis type before processing: {type(analysis)}")
            #print(f"DEBUG: Analysis keys before processing: {list(analysis.keys()) if isinstance(analysis, dict) else 'Not a dict'}")
                
            # Convert task_type string to enum
            task_type_str = analysis.get("task_type", "general")
            analysis["task_type"] = self._parse_task_type(task_type_str)
            
            # Add backward compatibility fields
            analysis["suggested_agent_count"] = len(analysis.get("suggested_agents", []))
            analysis["needs_parallel"] = any(
                step["type"] == "parallel" 
                for step in analysis.get("workflow_steps", [])
            )
            analysis["needs_debate"] = any(
                step["type"] == "debate" 
                for step in analysis.get("workflow_steps", [])
            )
            analysis["query"] = query
            
            return analysis
            
        except Exception as e:
            # Exit with error if model analysis fails
            print(f"\n❌ Model analysis failed: {e}")
            print("\nModel-based analysis is required but failed.")
            print("Please check your model configuration and try again.")
            raise RuntimeError(f"Model analysis failed: {e}") from e
    
    def _parse_task_type(self, task_type_str: str) -> TaskType:
        """Convert task type string to enum."""
        mapping = {
            "research": TaskType.RESEARCH,
            "code_review": TaskType.CODE_REVIEW,
            "design": TaskType.DESIGN,
            "analysis": TaskType.ANALYSIS,
            "planning": TaskType.PLANNING,
            "debate": TaskType.DEBATE,
            "implementation": TaskType.IMPLEMENTATION,
            "general": TaskType.GENERAL
        }
        return mapping.get(task_type_str.lower(), TaskType.GENERAL)


class ModelAnalyzer:
    """Model-based query analyzer (no fallback)."""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0.3):
        """Initialize the analyzer.
        
        Args:
            model: Model to use for analysis (defaults to config if not specified)
            temperature: Temperature for analysis (lower = more consistent)
        """
        self.model_analyzer = ModelBasedAnalyzer(model=model, temperature=temperature)
    
    async def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze query using model-based analysis.
        
        Model-based analysis is required. There is no fallback.
        """
        return await self.model_analyzer.analyze(query)