"""Base agent wrapper for Strands agents integration."""

from typing import Any, Optional, Dict, List
import asyncio
import copy
from dataclasses import dataclass, field
from io import StringIO
import sys

from strands import Agent, tool
from konseho.tools.parallel import ParallelExecutor


class AgentWrapper:
    """Wrapper for Strands agents to work within councils."""
    
    def __init__(self, agent: Agent, name: Optional[str] = None, **kwargs):
        """Initialize agent wrapper.
        
        Args:
            agent: Strands Agent instance
            name: Optional name for identification
            **kwargs: Additional attributes (e.g., expertise_level, domain)
        """
        self.agent = agent
        self.name = name or f"agent_{id(agent)}"
        self._history = []
        self.system_prompt_override = None
        self._parallel_executor = ParallelExecutor()
        
        # Add parallel tool to agent
        self._inject_parallel_tool()
        
        # Store any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    async def work_on(self, task: str, buffered: bool = True) -> str:
        """Have the agent work on a task asynchronously.
        
        Args:
            task: The task to work on
            buffered: Whether to buffer output to prevent interleaving
            
        Returns:
            The agent's response
        """
        # Lock to ensure sequential output when needed
        if not hasattr(self.__class__, '_output_lock'):
            self.__class__._output_lock = asyncio.Lock()
        
        if buffered:
            async with self.__class__._output_lock:
                # Capture stdout to prevent interleaved output
                buffer = StringIO()
                original_stdout = sys.stdout
                
                try:
                    sys.stdout = buffer
                    
                    # Strands agents are synchronous, so we run in executor
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.agent, task)
                    
                    # Get any printed output
                    captured_output = buffer.getvalue()
                    
                finally:
                    # Restore stdout before doing anything else
                    sys.stdout = original_stdout
                
                # Now print the captured output all at once
                if captured_output:
                    print(f"\n[{self.name}]:")
                    print(captured_output, end='')
                    sys.stdout.flush()  # Ensure output is displayed immediately
                
        else:
            # Non-buffered execution
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.agent, task)
        
        # Extract the message from the result
        if hasattr(result, 'message'):
            response = result.message
        else:
            response = str(result)
        
        self._history.append({
            "task": task,
            "response": response
        })
        
        return response
    
    def get_history(self) -> list:
        """Get the agent's task history."""
        return self._history.copy()
    
    def clone(self, new_name: str) -> 'AgentWrapper':
        """Create a clone of this agent wrapper with a new name.
        
        Args:
            new_name: Name for the cloned wrapper
            
        Returns:
            New AgentWrapper instance with cloned agent
        """
        # Clone the underlying agent
        cloned_agent = self._clone_agent(self.agent)
        
        # Get all custom attributes
        custom_attrs = {}
        for attr in dir(self):
            if not attr.startswith('_') and attr not in ['agent', 'name', 'work_on', 'get_history', 'clone']:
                value = getattr(self, attr)
                if not callable(value):
                    custom_attrs[attr] = value
        
        # Create new wrapper with cloned agent
        cloned_wrapper = AgentWrapper(cloned_agent, name=new_name, **custom_attrs)
        
        # Copy system prompt override if set
        if self.system_prompt_override:
            cloned_wrapper.system_prompt_override = self.system_prompt_override
        
        return cloned_wrapper
    
    def _inject_parallel_tool(self):
        """Add parallel execution tool to agent."""
        @tool
        def parallel(tool_name: str, args_list: List[Dict[str, Any]]) -> List[Any]:
            """Execute any tool multiple times in parallel with different arguments.
            
            Args:
                tool_name: Name of the tool to execute
                args_list: List of argument dictionaries for each execution
                
            Returns:
                List of results in the same order as arguments
                
            Example:
                parallel("file_read", [{"path": "file1.py"}, {"path": "file2.py"}])
            """
            # Find the tool in agent's tools
            target_tool = None
            for t in self.agent.tools:
                if hasattr(t, '__name__') and t.__name__ == tool_name:
                    target_tool = t
                    break
            
            if not target_tool:
                return [f"Error: Tool '{tool_name}' not found" for _ in args_list]
            
            return self._parallel_executor.execute_parallel(target_tool, args_list)
        
        # Add to agent's tools if not already present
        if hasattr(self.agent, 'tools') and isinstance(self.agent.tools, list):
            self.agent.tools.append(parallel)
    
    def _clone_agent(self, agent: Agent) -> Agent:
        """Clone a Strands agent preserving its configuration."""
        # Handle MockStrandsAgent for testing
        if hasattr(agent, '__class__') and agent.__class__.__name__ == 'MockStrandsAgent':
            # Create new instance with same config
            cloned = agent.__class__(agent.name, agent.response)
            if hasattr(agent, 'delay'):
                cloned.delay = agent.delay
            return cloned
        
        # For real Strands agents, we need to recreate with same config
        # This is a simplified version - in production would use Strands API
        try:
            # Try to access agent configuration
            config = {
                'name': getattr(agent, 'name', 'cloned_agent'),
                'model': getattr(agent, 'model', 'gpt-4'),
                'tools': getattr(agent, 'tools', []),
                'temperature': getattr(agent, 'temperature', 0.7),
            }
            
            # Copy system prompt if available
            if hasattr(agent, 'system_prompt'):
                config['system_prompt'] = agent.system_prompt
            
            # Deep copy any config dict
            if hasattr(agent, 'config'):
                config['config'] = copy.deepcopy(agent.config)
            
            # Create new agent (would use create_agent in real implementation)
            from konseho.agents.base import create_agent
            return create_agent(**config)
            
        except Exception:
            # Fallback: return the same agent (not ideal but safe)
            return agent


def create_agent(**config) -> Agent:
    """Create a new Strands agent with given configuration.
    
    Creates a real Strands agent using the provided configuration.
    """
    # Use configured model if not specified or if None
    model = config.get('model')
    if model is None:
        from konseho.config import create_model_from_config
        model = create_model_from_config()
    elif isinstance(model, str):
        # If model is a string (like "claude-opus-4-20250514"), create proper model object
        from konseho.config import create_model_from_config, ModelConfig, get_model_config
        base_config = get_model_config()
        # Override just the model_id
        model_config = ModelConfig(
            provider=base_config.provider,
            model_id=model,
            api_key=base_config.api_key,
            additional_args=base_config.additional_args
        )
        model = create_model_from_config(model_config)
    
    tools = config.get('tools', [])
    name = config.get('name', 'agent')
    
    # Create Strands agent with system prompt if provided
    agent_args = {
        'model': model,
        'tools': tools,
        # Always set callback_handler to prevent default PrintingCallbackHandler
        # which conflicts with our buffering in AgentWrapper
        'callback_handler': config.get('callback_handler', None)
    }
    
    # Always inject current date/time information
    from datetime import datetime
    current_datetime = datetime.now()
    date_info = f"\n\nCurrent date and time: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Add system prompt to agent creation
    if 'system_prompt' in config:
        # Append date info to existing system prompt
        agent_args['system_prompt'] = config['system_prompt'] + date_info
    else:
        # Create minimal system prompt with just date info
        agent_args['system_prompt'] = f"You are a helpful AI assistant.{date_info}"
    
    # Create agent with all args
    agent = Agent(**agent_args)
    
    # Set additional attributes if provided
    if hasattr(agent, 'name'):
        agent.name = name
    if 'temperature' in config and hasattr(agent, 'temperature'):
        agent.temperature = config['temperature']
    
    return agent