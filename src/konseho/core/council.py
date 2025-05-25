"""Council orchestrator for managing multi-agent workflows."""

from typing import List, Optional, Any, Dict, Union
import asyncio
import logging

from strands import Agent
from .context import Context
from .steps import Step, DebateStep
from ..agents.base import AgentWrapper
from ..execution.events import EventEmitter

logger = logging.getLogger(__name__)


class Council:
    """Orchestrates multiple agents working together through defined steps."""
    
    def __init__(
        self,
        name: str = "council",
        steps: Optional[List[Step]] = None,
        agents: Optional[List[Union[Agent, AgentWrapper]]] = None,
        context: Optional[Context] = None,
        error_strategy: str = "halt",
        workflow: str = "sequential"
    ):
        """Initialize a council.
        
        Args:
            name: Council identifier
            steps: Ordered list of execution steps
            agents: List of agents (creates a DebateStep if provided without steps)
            context: Shared context (created if not provided)
            error_strategy: How to handle errors (halt, continue, retry, fallback)
            workflow: Workflow type (sequential, iterative)
        """
        self.name = name
        self.context = context or Context()
        self.error_strategy = error_strategy
        self.workflow = workflow
        self._event_emitter = EventEmitter()
        
        # Handle initialization with agents or steps
        if steps is not None:
            self.steps = steps
        elif agents is not None:
            # Create a single DebateStep with all agents
            self.steps = [DebateStep(agents)]
        else:
            self.steps = []
    
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
                    elif self.error_strategy == "continue":
                        # Log error and continue to next step
                        logger.warning(f"Step {i} failed with error: {e}, continuing...")
                        self.context.add_result(f"step_{i}", {"error": str(e)})
                        continue
                    elif self.error_strategy == "retry":
                        # Simple retry once
                        try:
                            result = await step.execute(task, self.context)
                            self.context.add_result(f"step_{i}", result)
                            self._event_emitter.emit("step:complete", {"step": i, "result": result})
                        except Exception as retry_error:
                            if self.error_strategy == "halt":
                                raise
                            else:
                                logger.warning(f"Step {i} retry failed: {retry_error}")
                                self.context.add_result(f"step_{i}", {"error": str(retry_error)})
                    elif self.error_strategy == "fallback":
                        # Use a default/fallback result
                        fallback_result = {"status": "fallback", "message": f"Step failed: {str(e)}"}
                        self.context.add_result(f"step_{i}", fallback_result)
                        self._event_emitter.emit("step:fallback", {"step": i, "error": str(e)})
            
            final_result = self.context.get_summary()
            self._event_emitter.emit("council:complete", {"result": final_result})
            return final_result
            
        except Exception as e:
            self._event_emitter.emit("council:error", {"error": str(e)})
            raise
    
    def run(self, task: str) -> Dict[str, Any]:
        """Synchronous wrapper for execute."""
        return asyncio.run(self.execute(task))
    
    async def stream_execute(self, task: str):
        """Execute the council workflow with streaming events.
        
        Yields:
            CouncilEvent: Events as they occur during execution
        """
        # This would be implemented with proper async generators
        # For now, just execute normally
        result = await self.execute(task)
        yield {"type": "complete", "result": result}
    
    def handle_error(self, error: Exception, context: Context) -> None:
        """Handle errors according to the configured strategy.
        
        Args:
            error: The exception that occurred
            context: Current council context
        """
        logger.error(f"Council error: {error}")
        self._event_emitter.emit("council:error", {
            "error": str(error),
            "strategy": self.error_strategy,
            "context_summary": context.get_summary()
        })