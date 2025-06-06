"""Error handling component for the Council system."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import TYPE_CHECKING, Any

from konseho.core.steps import StepResult
from konseho.protocols import IEventEmitter, IStep, IStepResult

if TYPE_CHECKING:
    from konseho.core.context import Context

logger = logging.getLogger(__name__)


class ErrorStrategy(str, Enum):
    """Strategies for handling errors during execution."""

    HALT = "halt"
    CONTINUE = "continue"
    RETRY = "retry"
    FALLBACK = "fallback"


class ErrorHandler:
    """Handles error strategies and retry logic for Council execution."""

    def __init__(
        self,
        error_strategy: ErrorStrategy = ErrorStrategy.HALT,
        max_retries: int = 3,
        fallback_handler: Callable[[Exception, IStep, str, "Context"], Coroutine[Any, Any, IStepResult]] | None = None,
        event_emitter: IEventEmitter | None = None,
    ):
        """Initialize the ErrorHandler.

        Args:
            error_strategy: Strategy for handling errors
            max_retries: Maximum retry attempts for retry strategy
            fallback_handler: Custom handler for fallback strategy
            event_emitter: Optional event emitter for error events
        """
        self.error_strategy = error_strategy
        self.max_retries = max_retries
        self.fallback_handler = fallback_handler
        self.event_emitter = event_emitter

    async def handle_step_error(
        self,
        error: Exception,
        step: IStep,
        task: str,
        context: "Context",
        attempt: int = 0,
    ) -> IStepResult | None:
        """Handle an error that occurred during step execution.

        Args:
            error: The exception that was raised
            step: The step that failed
            task: The task being executed
            context: The execution context
            attempt: Current retry attempt number

        Returns:
            Optional step result based on error strategy

        Raises:
            Exception: Re-raises the error if strategy is HALT
        """
        logger.error(f"Error in step {step.name}: {error}")

        if self.event_emitter:
            self.event_emitter.emit(
                "step_error",
                {
                    "step": step.name,
                    "error": str(error),
                    "attempt": attempt,
                    "strategy": self.error_strategy,
                },
            )

        if self.error_strategy == ErrorStrategy.HALT:
            raise error

        elif self.error_strategy == ErrorStrategy.CONTINUE:
            logger.warning(f"Continuing after error in {step.name}: {error}")
            return StepResult(
                output=f"Step failed with error: {error}",
                metadata={
                    "error": str(error),
                    "skipped": True,
                    "step_name": step.name,
                    "agents_involved": [],
                },
            )

        elif self.error_strategy == ErrorStrategy.RETRY:
            if attempt < self.max_retries:
                logger.info(
                    f"Retrying {step.name} (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(2**attempt)  # Exponential backoff

                # Return None to signal retry
                return None
            else:
                logger.error(f"Max retries exceeded for {step.name}")
                raise error

        elif self.error_strategy == ErrorStrategy.FALLBACK:
            if self.fallback_handler:
                logger.info(f"Using fallback handler for {step.name}")
                return await self.fallback_handler(error, step, task, context)
            else:
                logger.warning(
                    "No fallback handler configured, continuing after error"
                )
                return StepResult(
                    output=f"Step failed with error: {error} (no fallback available)",
                    metadata={
                        "error": str(error),
                        "skipped": True,
                        "step_name": step.name,
                        "agents_involved": [],
                    },
                )

        # Should not reach here
        raise ValueError(f"Unknown error strategy: {self.error_strategy}")

    async def execute_with_error_handling(
        self,
        step: IStep,
        task: str,
        context: "Context",
        execute_fn: Callable[[IStep, str, "Context"], Coroutine[Any, Any, IStepResult]],
    ) -> IStepResult:
        """Execute a step with error handling applied.

        Args:
            step: The step to execute
            task: The task to execute
            context: The execution context
            execute_fn: The function to execute the step

        Returns:
            The step result

        Raises:
            Exception: If error strategy is HALT and an error occurs
        """
        attempt = 0

        while True:
            try:
                result = await execute_fn(step, task, context)
                if attempt > 0 and self.event_emitter:
                    self.event_emitter.emit(
                        "step_retry_success",
                        {"step": step.name, "attempts": attempt + 1},
                    )
                return result

            except Exception as e:
                result = await self.handle_step_error(e, step, task, context, attempt)

                if result is None and self.error_strategy == ErrorStrategy.RETRY:
                    # Retry signal
                    attempt += 1
                    continue
                elif result is not None:
                    # Error was handled with a result
                    return result
                else:
                    # Error should be re-raised
                    raise
