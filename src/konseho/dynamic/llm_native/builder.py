"""Builder for creating councils from LLM specifications."""
import logging
from typing import Any, Dict, List, Optional

from konseho.agents.base import Agent
from konseho.core.council import Council
from konseho.core.steps import Step, DebateStep, ParallelStep, SplitStep
from konseho.factories import CouncilFactory, CouncilDependencies
from konseho.dynamic.llm_native.schemas import (
    CouncilSpec,
    AgentSpec,
    StepSpec,
    StepType,
    ModelChoice
)
from konseho.tools.file_ops import file_read, file_write
from konseho.tools.search_tool import web_search
from konseho.tools.http_ops import http_get, http_post
from konseho.tools.code_ops import code_edit, code_insert


logger = logging.getLogger(__name__)


# Default tool mapping
DEFAULT_TOOLS = {
    "read_file": file_read,
    "write_file": file_write,
    "web_search": web_search,
    "http_get": http_get,
    "http_post": http_post,
    "code_edit": code_edit,
    "code_insert": code_insert,
}

# Model mapping (can be extended with actual model instances)
MODEL_MAPPING = {
    ModelChoice.CLAUDE_3_HAIKU: "claude-3-5-haiku-20241022",
    ModelChoice.CLAUDE_3_SONNET: "claude-3-5-sonnet-20241022",
    ModelChoice.CLAUDE_3_OPUS: "claude-3-opus-20240229",
    ModelChoice.GPT_4: "gpt-4",
    ModelChoice.GPT_4_TURBO: "gpt-4-turbo",
    ModelChoice.GPT_35_TURBO: "gpt-3.5-turbo",
}


class LLMCouncilBuilder:
    """Builds councils from LLM-generated specifications."""
    
    def __init__(
        self,
        tool_mapping: Optional[Dict[str, Any]] = None,
        model_mapping: Optional[Dict[str, Any]] = None
    ):
        """Initialize the builder.
        
        Args:
            tool_mapping: Custom tool name to tool instance mapping
            model_mapping: Custom model name to model instance mapping
        """
        self.tool_mapping = tool_mapping or DEFAULT_TOOLS
        self.model_mapping = model_mapping or MODEL_MAPPING
    
    async def build(self, spec: CouncilSpec) -> Council:
        """Build a council from the specification.
        
        Args:
            spec: The council specification
            
        Returns:
            A configured Council instance
        """
        logger.info(f"Building council: {spec.name}")
        
        # Create agents
        agents = {}
        for agent_spec in spec.agents:
            agent = await self._create_agent(agent_spec)
            agents[agent_spec.id] = agent
        
        # Create steps
        steps = []
        for step_spec in spec.steps:
            step = self._create_step(step_spec, agents)
            steps.append(step)
        
        # Create council using factory
        factory = CouncilFactory()
        council = factory.create_council(
            name=spec.name,
            steps=steps
        )
        
        logger.info(f"Successfully built council with {len(agents)} agents and {len(steps)} steps")
        return council
    
    async def _create_agent(self, spec: AgentSpec) -> Agent:
        """Create an agent from specification.
        
        Args:
            spec: Agent specification
            
        Returns:
            Configured Agent instance
        """
        # Resolve model
        model = self._resolve_model(spec.model)
        
        # Resolve tools
        tools = self._resolve_tools(spec.tools)
        
        # Use konseho's create_agent helper
        from konseho.agents.base import create_agent
        
        agent = create_agent(
            name=spec.id,
            model=model,
            tools=tools,
            system_prompt=spec.prompt,
            temperature=spec.temperature
        )
        
        logger.debug(f"Created agent: {spec.id} with {len(tools)} tools")
        return agent
    
    def _create_step(self, spec: StepSpec, agents: Dict[str, Agent]) -> Step:
        """Create a step from specification.
        
        Args:
            spec: Step specification
            agents: Dictionary of agent_id to Agent instances
            
        Returns:
            Configured Step instance
        """
        # Get agents for this step
        step_agents = [agents[agent_id] for agent_id in spec.agents]
        
        # Create appropriate step type
        if spec.type == StepType.DEBATE:
            rounds = spec.config.get("rounds", 2)
            step = DebateStep(
                agents=step_agents,
                rounds=rounds
            )
        
        elif spec.type == StepType.PARALLEL:
            step = ParallelStep(
                agents=step_agents
            )
        
        elif spec.type == StepType.SPLIT:
            # For split steps, we need a task splitter function
            # For now, use a simple splitter
            def task_splitter(task: str, num_agents: int) -> List[str]:
                # Simple splitting logic - can be enhanced
                return [f"{task} (part {i+1}/{num_agents})" for i in range(num_agents)]
            
            # SplitStep needs a single agent template, use the first agent
            if not step_agents:
                raise ValueError("Split step requires at least one agent")
            
            step = SplitStep(
                agent_template=step_agents[0],
                task_splitter=task_splitter
            )
        
        elif spec.type == StepType.SYNTHESIZE:
            # Synthesize is just a parallel step with one agent
            step = ParallelStep(
                agents=step_agents
            )
        
        elif spec.type in [StepType.SEQUENCE, StepType.VOTE, StepType.REFINE]:
            # For now, implement these as parallel steps
            # TODO: Implement specific step types
            step = ParallelStep(
                agents=step_agents
            )
        
        else:
            raise ValueError(f"Unknown step type: {spec.type}")
        
        logger.debug(f"Created {spec.type} step with {len(step_agents)} agents")
        return step
    
    def _resolve_model(self, model_name: str) -> Any:
        """Resolve model name to model instance.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model instance or string identifier
        """
        # For now, return the mapped model string
        # In a real implementation, this would return actual model instances
        if model_name in self.model_mapping:
            return self.model_mapping[model_name]
        
        # If not in mapping, return as-is (might be a custom model string)
        return model_name
    
    def _resolve_tools(self, tool_names: List[str]) -> List[Any]:
        """Resolve tool names to tool instances.
        
        Args:
            tool_names: List of tool names
            
        Returns:
            List of tool instances
        """
        tools = []
        for name in tool_names:
            if name in self.tool_mapping:
                tools.append(self.tool_mapping[name])
            else:
                logger.warning(f"Unknown tool: {name}, skipping")
        
        return tools
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tool_mapping.keys())
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names.
        
        Returns:
            List of model names
        """
        return [m.value for m in ModelChoice]