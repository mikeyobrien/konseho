"""Base agent wrapper for Strands agents integration."""

from typing import Any, Optional, Dict, List
import asyncio
import copy
from dataclasses import dataclass, field
from io import StringIO
import sys

from strands import Agent


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
                    print(f"\n[{self.name}]:\n{captured_output}", end='')
                
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
    
    tools = config.get('tools', [])
    name = config.get('name', 'agent')
    
    # Create Strands agent with system prompt if provided
    agent_args = {
        'model': model,
        'tools': tools
    }
    
    # Add system prompt to agent creation if provided
    if 'system_prompt' in config:
        agent_args['system_prompt'] = config['system_prompt']
    
    # Create agent with all args
    agent = Agent(**agent_args)
    
    # Set additional attributes if provided
    if hasattr(agent, 'name'):
        agent.name = name
    if 'temperature' in config and hasattr(agent, 'temperature'):
        agent.temperature = config['temperature']
    
    return agent