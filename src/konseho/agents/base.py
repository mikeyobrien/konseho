"""Base agent wrapper for Strands agents integration."""

from typing import Any, Optional, Dict, List
import asyncio
import copy
from dataclasses import dataclass, field

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
    
    async def work_on(self, task: str) -> str:
        """Have the agent work on a task asynchronously."""
        # Strands agents are synchronous, so we run in executor
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
    
    This is a placeholder for actual Strands agent creation.
    In production, this would use the Strands SDK.
    """
    # Mock implementation for testing
    class MockConfiguredAgent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.call_count = 0
            self.call_history = []
        
        def __call__(self, prompt: str):
            self.call_count += 1
            self.call_history.append(prompt)
            return f"Response from {getattr(self, 'name', 'agent')}"
    
    return MockConfiguredAgent(**config)