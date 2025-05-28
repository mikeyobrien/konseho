"""Step execution engine for handling the mechanics of step execution."""

import logging
from typing import TYPE_CHECKING

from konseho.protocols import IEventEmitter, IStep, IStepResult

if TYPE_CHECKING:
    from konseho.core.context import Context
    from konseho.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class StepExecutionEngine:
    """Handles the mechanics of step execution with error handling and events."""

    def __init__(
        self,
        error_handler: "ErrorHandler",
        event_emitter: IEventEmitter | None = None,
    ):
        """Initialize the execution engine.

        Args:
            error_handler: Handler for error strategies
            event_emitter: Optional event emitter for step events
        """
        self.error_handler = error_handler
        self.event_emitter = event_emitter

    async def execute_step(
        self,
        step: IStep,
        task: str,
        context: "Context",
    ) -> IStepResult:
        """Execute a step with error handling and event emission.

        Args:
            step: The step to execute
            task: The task to execute
            context: The execution context

        Returns:
            The step result

        Raises:
            Exception: If error strategy is HALT and an error occurs
        """
        step_name = step.name

        # Emit start event
        if self.event_emitter:
            await self.event_emitter.emit_async(
                "step_start",
                {
                    "step": step_name,
                    "task": task[:100],  # Truncate for logging
                },
            )

        try:
            # Execute step using error handler
            result = await self.error_handler.execute_with_error_handling(
                step,
                task,
                context,
                self._execute_step_impl,
            )

            # Emit complete event
            if self.event_emitter:
                await self.event_emitter.emit_async(
                    "step_complete",
                    {
                        "step": step_name,
                        "result": {
                            "output": result.output[:200] if result.output else "",
                            "success": result.success,
                            "metadata": result.metadata,
                        },
                    },
                )

            return result

        except Exception as e:
            # Emit error event (error handler already logged)
            if self.event_emitter:
                await self.event_emitter.emit_async(
                    "step_failed",
                    {
                        "step": step_name,
                        "error": str(e),
                    },
                )
            raise

    async def _execute_step_impl(
        self,
        step: IStep,
        task: str,
        context: "Context",
    ) -> IStepResult:
        """Implementation of step execution without error handling.

        Args:
            step: The step to execute
            task: The task to execute
            context: The execution context

        Returns:
            The step result
        """
        # Validate step before execution
        validation_errors = step.validate()
        if validation_errors:
            raise ValueError(f"Step validation failed: {', '.join(validation_errors)}")

        # Execute the step
        result = await step.execute(task, context)

        # Log execution details
        logger.info(
            f"Step {step.name} completed. "
            f"Output length: {len(result.output) if result.output else 0}"
        )

        return result

