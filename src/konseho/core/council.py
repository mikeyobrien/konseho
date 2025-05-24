"""Council orchestrator for managing multi-agent workflows."""

from typing import List, Optional, Any, Dict
import asyncio
import logging

from strands import Agent
from .context import Context
from .steps import Step
from ..execution.events import EventEmitter

logger = logging.getLogger(__name__)


class Council:
    """Orchestrates multiple agents working together through defined steps."""
    
    def __init__(
        self,
        name: str,
        steps: List[Step],
        context: Optional[Context] = None,
        error_strategy: str = "halt",
    ):
        """Initialize a council.
        
        Args:
            name: Council identifier
            steps: Ordered list of execution steps
            context: Shared context (created if not provided)
            error_strategy: How to handle errors (halt, continue, retry)
        """
        self.name = name
        self.steps = steps
        self.context = context or Context()
        self.error_strategy = error_strategy
        self._event_emitter = EventEmitter()
    
    async def execute(self, task: str) -> Dict[str, Any]:
        """Execute the council workflow with the given task."""
        self._event_emitter.emit("council:start", {"council": self.name, "task": task})
        
        try:
            for i, step in enumerate(self.steps):
                self._event_emitter.emit("step:start", {"step": i, "type": type(step).__name__})
                
                try:
                    result = await step.execute(task, self.context)
                    self.context.add_result(f"step_{i}", result)
                    self._event_emitter.emit("step:complete", {"step": i, "result": result})
                except Exception as e:
                    self._event_emitter.emit("step:error", {"step": i, "error": str(e)})
                    
                    if self.error_strategy == "halt":
                        raise
                    elif self.error_strategy == "retry":
                        # Simple retry once
                        result = await step.execute(task, self.context)
                        self.context.add_result(f"step_{i}", result)
            
            final_result = self.context.get_summary()
            self._event_emitter.emit("council:complete", {"result": final_result})
            return final_result
            
        except Exception as e:
            self._event_emitter.emit("council:error", {"error": str(e)})
            raise
    
    def run(self, task: str) -> Dict[str, Any]:
        """Synchronous wrapper for execute."""
        return asyncio.run(self.execute(task))