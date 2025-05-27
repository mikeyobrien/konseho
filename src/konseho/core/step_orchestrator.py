"""Step orchestration component for the Council system."""

from typing import List, Optional, TYPE_CHECKING
import logging

from konseho.protocols import IEventEmitter, IStep, IStepResult, IOutputManager
from konseho.core.error_handler import ErrorHandler

if TYPE_CHECKING:
    from konseho.core.context import Context

logger = logging.getLogger(__name__)


class StepOrchestrator:
    """Orchestrates the execution of steps in sequence."""
    
    def __init__(
        self,
        steps: List[IStep],
        event_emitter: Optional[IEventEmitter] = None,
        output_manager: Optional[IOutputManager] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """Initialize the StepOrchestrator.
        
        Args:
            steps: List of steps to execute
            event_emitter: Optional event emitter for step events
            output_manager: Optional output manager
            error_handler: Optional error handler
        """
        self.steps = steps
        self.event_emitter = event_emitter
        self.output_manager = output_manager
        self.error_handler = error_handler or ErrorHandler()
        
    async def execute_steps(self, task: str, context: "Context") -> List[IStepResult]:
        """Execute all steps in sequence.
        
        Args:
            task: The task to execute
            context: The execution context
            
        Returns:
            List of step results
        """
        results = []
        
        if self.event_emitter:
            self.event_emitter.emit("council_started", {"task": task})
        
        for i, step in enumerate(self.steps):
            if self.event_emitter:
                self.event_emitter.emit("step_started", {
                    "step": step.name,
                    "index": i,
                    "total": len(self.steps)
                })
            
            # Execute step with error handling
            result = await self.error_handler.execute_with_error_handling(
                step,
                task,
                context,
                self._execute_single_step
            )
            
            results.append(result)
            
            # Update context with result
            context.add_result(f"step_{i}", result)
            
            if self.event_emitter:
                self.event_emitter.emit("step_completed", {
                    "step": step.name,
                    "result": result.output[:200] + "..." if len(result.output) > 200 else result.output
                })
            
        
        if self.event_emitter:
            self.event_emitter.emit("council_completed", {
                "task": task,
                "steps_completed": len(results)
            })
        
        return results
    
    async def _execute_single_step(
        self,
        step: IStep,
        task: str,
        context: "Context"
    ) -> IStepResult:
        """Execute a single step.
        
        Args:
            step: The step to execute
            task: The task to execute
            context: The execution context
            
        Returns:
            The step result
        """
        logger.info(f"Executing step: {step.name}")
        
        # Validate step before execution
        step.validate()
        
        # Execute the step
        result = await step.execute(task, context)
        
        logger.info(f"Step {step.name} completed")
        
        return result