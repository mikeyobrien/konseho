"""Step orchestration component for the Council system."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from konseho.core.error_handler import ErrorHandler
from konseho.protocols import IEventEmitter, IOutputManager, IStep, IStepResult, JSON
if TYPE_CHECKING:
    from konseho.core.context import Context
logger = logging.getLogger(__name__)


class StepOrchestrator:
    """Orchestrates the execution of steps in sequence."""

    def __init__(self, steps: list[IStep], event_emitter: (IEventEmitter |
        None)=None, output_manager: (IOutputManager | None)=None,
        error_handler: (ErrorHandler | None)=None):
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

    async def execute_steps(self, task: str, context: 'Context',
        council_name: str='council') ->list[IStepResult]:
        """Execute all steps in sequence.

        Args:
            task: The task to execute
            context: The execution context
            council_name: Name of the council executing the steps

        Returns:
            List of step results
        """
        results = []
        if self.event_emitter:
            self.event_emitter.emit('council:start', {'task': task,
                'council': council_name})
        for i, step in enumerate(self.steps):
            if self.event_emitter:
                self.event_emitter.emit('step:start', {'step': i, 'type':
                    step.__class__.__name__, 'index': i, 'total': len(self.
                    steps)})
            result = await self.error_handler.execute_with_error_handling(step,
                task, context, self._execute_single_step)
            results.append(result)
            # Convert IStepResult to JSON-compatible dict for context
            from typing import cast
            result_dict: JSON = {
                'output': result.output,
                'metadata': cast(JSON, result.metadata),
                'success': result.success
            }
            context.add_result(result_dict)
            if self.event_emitter:
                self.event_emitter.emit('step:complete', {'step': i,
                    'type': step.__class__.__name__, 'result': result_dict})
        if self.event_emitter:
            self.event_emitter.emit('council:complete', {'task': task,
                'council': council_name, 'steps_completed': len(results)})
        return results

    async def _execute_single_step(self, step: IStep, task: str, context:
        'Context') ->IStepResult:
        """Execute a single step.

        Args:
            step: The step to execute
            task: The task to execute
            context: The execution context

        Returns:
            The step result
        """
        logger.info(f'Executing step: {step.name}')
        step.validate()
        result = await step.execute(task, context)
        logger.info(f'Step {step.name} completed')
        return result
