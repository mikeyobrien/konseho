"""Base agent wrapper for Strands agents integration."""

from typing import Any, Optional, Dict
import asyncio

from strands import Agent


class AgentWrapper:
    """Wrapper for Strands agents to work within councils."""
    
    def __init__(self, agent: Agent, name: Optional[str] = None):
        """Initialize agent wrapper.
        
        Args:
            agent: Strands Agent instance
            name: Optional name for identification
        """
        self.agent = agent
        self.name = name or f"agent_{id(agent)}"
        self._history = []
    
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