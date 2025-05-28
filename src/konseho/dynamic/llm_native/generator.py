"""LLM-based council specification generator."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from konseho.dynamic.llm_native.schemas import CouncilSpec, extract_json_from_response


logger = logging.getLogger(__name__)


# Example councils for the LLM to learn from
EXAMPLE_COUNCILS = [
    {
        "query": "Review this Python code for security vulnerabilities",
        "council": {
            "name": "SecurityReviewCouncil",
            "description": "Reviews code for security vulnerabilities",
            "agents": [
                {
                    "id": "vuln_scanner",
                    "prompt": "You are a security expert focused on finding vulnerabilities. Analyze code for OWASP top 10 issues, injection flaws, and authentication weaknesses.",
                    "model": "claude-3-sonnet",
                    "temperature": 0.2,
                    "tools": ["read_file", "search_code"]
                },
                {
                    "id": "architecture_reviewer",
                    "prompt": "You review system architecture for security best practices. Focus on defense in depth, principle of least privilege, and secure design patterns.",
                    "temperature": 0.3,
                    "tools": ["read_file"]
                }
            ],
            "steps": [
                {
                    "type": "parallel",
                    "agents": ["vuln_scanner", "architecture_reviewer"],
                    "task_template": "Analyze {input} for security issues in your domain"
                },
                {
                    "type": "debate",
                    "agents": ["vuln_scanner", "architecture_reviewer"],
                    "task_template": "Discuss the findings and prioritize the top security issues",
                    "config": {"rounds": 2}
                },
                {
                    "type": "synthesize",
                    "agents": ["architecture_reviewer"],
                    "task_template": "Create a unified security report with actionable recommendations based on {context}"
                }
            ]
        }
    },
    {
        "query": "Design a REST API for a todo application",
        "council": {
            "name": "APIDesignCouncil",
            "description": "Designs REST APIs with best practices",
            "agents": [
                {
                    "id": "api_designer",
                    "prompt": "You are an API design expert. Focus on RESTful principles, clear resource modeling, and consistent naming conventions.",
                    "temperature": 0.7,
                    "tools": ["web_search"]
                },
                {
                    "id": "backend_engineer",
                    "prompt": "You are a backend engineer. Consider implementation details, performance, scalability, and database design.",
                    "temperature": 0.6
                },
                {
                    "id": "security_consultant",
                    "prompt": "You are a security consultant. Focus on authentication, authorization, rate limiting, and API security best practices.",
                    "temperature": 0.4
                }
            ],
            "steps": [
                {
                    "type": "parallel",
                    "agents": ["api_designer", "backend_engineer", "security_consultant"],
                    "task_template": "Design a REST API for {input} from your perspective"
                },
                {
                    "type": "debate",
                    "agents": ["api_designer", "backend_engineer", "security_consultant"],
                    "task_template": "Discuss and refine the API design, addressing concerns from all perspectives",
                    "config": {"rounds": 3}
                },
                {
                    "type": "synthesize",
                    "agents": ["api_designer"],
                    "task_template": "Create the final API specification incorporating all feedback from {context}"
                }
            ]
        }
    }
]


GENERATOR_PROMPT = """You are a council configuration generator for a multi-agent system.

Generate a JSON specification for a council that will handle the user's request.

COUNCIL STRUCTURE:
- name: Descriptive name for the council
- description: Brief description of the council's purpose
- agents: List of agent specifications
- steps: List of workflow steps

AGENT SPECIFICATION:
- id: Unique identifier (snake_case, used in steps)
- prompt: Clear system prompt describing the agent's role and approach
- model: (optional) "claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
- temperature: (optional) 0.0-1.0, lower for analytical tasks, higher for creative tasks
- tools: (optional) List of tool names the agent can use

STEP TYPES:
- parallel: Multiple agents work simultaneously
- sequence: Agents work one after another
- debate: Agents discuss and refine ideas
- synthesize: One agent summarizes all findings
- split: Divide work dynamically
- vote: Agents vote on options
- refine: Iteratively improve a solution

STEP SPECIFICATION:
- type: One of the step types above
- agents: List of agent IDs participating
- task_template: Template with {{input}} for user query and {{context}} for accumulated context
- config: (optional) Step-specific configuration (e.g., rounds for debate)

AVAILABLE TOOLS:
{available_tools}

GUIDELINES:
1. Use 2-4 agents for most tasks
2. Keep agent prompts focused and specific
3. Design workflows that make sense for the task
4. Use appropriate models and temperatures
5. Only assign tools that are relevant to the agent's role

EXAMPLES:
{examples}

USER REQUEST: {query}

Generate a JSON council specification (no markdown, no explanation, just valid JSON):
"""


class LLMCouncilGenerator:
    """Generates council specifications using an LLM."""
    
    def __init__(
        self,
        model: Any,
        available_tools: Optional[List[str]] = None,
        max_retries: int = 3
    ):
        """Initialize the generator.
        
        Args:
            model: The LLM model to use for generation
            available_tools: List of available tool names
            max_retries: Maximum number of retries on failure
        """
        self.model = model
        self.available_tools = available_tools or [
            "read_file", "search_code", "web_search", "analyze_dependencies"
        ]
        self.max_retries = max_retries
    
    async def generate_council_spec(self, query: str) -> CouncilSpec:
        """Generate a council specification for the given query.
        
        Args:
            query: The user's request
            
        Returns:
            A validated CouncilSpec
            
        Raises:
            ValueError: If unable to generate valid specification
        """
        examples_json = json.dumps(EXAMPLE_COUNCILS, indent=2)
        tools_list = ", ".join(self.available_tools)
        
        prompt = GENERATOR_PROMPT.format(
            available_tools=tools_list,
            examples=examples_json,
            query=query
        )
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Add error feedback if retrying
                if attempt > 0 and last_error:
                    prompt += f"\n\nPREVIOUS ATTEMPT FAILED: {last_error}\nPlease provide valid JSON only."
                
                # Get LLM response
                response = await self.model.work_on(prompt)
                
                # Extract JSON
                json_data = extract_json_from_response(response)
                
                # Validate with Pydantic
                spec = CouncilSpec(**json_data)
                
                logger.info(f"Successfully generated council: {spec.name}")
                return spec
                
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt < self.max_retries - 1:
                    # Brief delay before retry
                    await asyncio.sleep(0.5)
        
        raise ValueError(f"Failed to generate valid council after {self.max_retries} attempts. Last error: {last_error}")