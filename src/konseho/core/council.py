"""Council orchestrator for managing multi-agent workflows."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from strands import Agent

from ..agents.base import AgentWrapper
from ..execution.events import EventEmitter
from ..factories import CouncilDependencies
from .context import Context
from .output_manager import OutputManager
from .steps import DebateStep, Step

logger = logging.getLogger(__name__)


class Council:
    """Orchestrates multiple agents working together through defined steps."""

    def __init__(
        self,
        name: str = "council",
        steps: list[Step] | None = None,
        agents: list[Agent | AgentWrapper] | None = None,
        context: Context | None = None,
        dependencies: CouncilDependencies | None = None,
        error_strategy: str = "halt",
        workflow: str = "sequential",
        save_outputs: bool = False,
        output_dir: str | Path | None = None,
    ):
        """Initialize a council.

        Args:
            name: Council identifier
            steps: Ordered list of execution steps
            agents: List of agents (creates a DebateStep if provided without steps)
            context: Shared context (created if not provided, ignored if dependencies provided)
            dependencies: Container with all dependencies (optional, for dependency injection)
            error_strategy: How to handle errors (halt, continue, retry, fallback)
            workflow: Workflow type (sequential, iterative)
            save_outputs: Whether to automatically save outputs
            output_dir: Directory for saving outputs (default: "council_outputs")
        """
        self.name = name
        self.error_strategy = error_strategy
        self.workflow = workflow
        self.save_outputs = save_outputs

        # Handle dependency injection
        if dependencies:
            # Use injected dependencies
            self.context = dependencies.context
            self._event_emitter = dependencies.event_emitter
            self.output_manager = dependencies.output_manager
        else:
            # Legacy initialization (backward compatibility)
            self.context = context or Context()
            self._event_emitter = EventEmitter()
            self.output_manager = (
                OutputManager(output_dir or "council_outputs") if save_outputs else None
            )

        # Handle initialization with agents or steps
        if steps is not None:
            self.steps = steps
        elif agents is not None:
            # Create a single DebateStep with all agents
            self.steps = [DebateStep(agents)]
        else:
            self.steps = []

    async def execute(self, task: str) -> dict[str, Any]:
        """Execute the council workflow with the given task."""
        self._event_emitter.emit("council:start", {"council": self.name, "task": task})

        try:
            for i, step in enumerate(self.steps):
                self._event_emitter.emit(
                    "step:start", {"step": i, "type": type(step).__name__}
                )

                try:
                    result = await step.execute(task, self.context)
                    self.context.add_result(f"step_{i}", result)
                    self._event_emitter.emit(
                        "step:complete", {"step": i, "result": result}
                    )
                except Exception as e:
                    self._event_emitter.emit("step:error", {"step": i, "error": str(e)})

                    if self.error_strategy == "halt":
                        raise
                    elif self.error_strategy == "continue":
                        # Log error and continue to next step
                        logger.warning(
                            f"Step {i} failed with error: {e}, continuing..."
                        )
                        self.context.add_result(f"step_{i}", {"error": str(e)})
                        continue
                    elif self.error_strategy == "retry":
                        # Simple retry once
                        try:
                            result = await step.execute(task, self.context)
                            self.context.add_result(f"step_{i}", result)
                            self._event_emitter.emit(
                                "step:complete", {"step": i, "result": result}
                            )
                        except Exception as retry_error:
                            if self.error_strategy == "halt":
                                raise
                            else:
                                logger.warning(f"Step {i} retry failed: {retry_error}")
                                self.context.add_result(
                                    f"step_{i}", {"error": str(retry_error)}
                                )
                    elif self.error_strategy == "fallback":
                        # Use a default/fallback result
                        fallback_result = {
                            "status": "fallback",
                            "message": f"Step failed: {str(e)}",
                        }
                        self.context.add_result(f"step_{i}", fallback_result)
                        self._event_emitter.emit(
                            "step:fallback", {"step": i, "error": str(e)}
                        )

            final_result = self.context.get_summary()
            self._event_emitter.emit("council:complete", {"result": final_result})

            # Save output if enabled
            if self.save_outputs and self.output_manager:
                try:
                    # Collect metadata
                    metadata = {
                        "error_strategy": self.error_strategy,
                        "workflow": self.workflow,
                        "num_steps": len(self.steps),
                        "agents": self._get_agent_names(),
                    }

                    # Save both JSON and formatted versions
                    output_path = self.output_manager.save_formatted_output(
                        task=task,
                        result=final_result,
                        council_name=self.name,
                        metadata=metadata,
                    )

                    logger.info(f"Council output saved to: {output_path}")
                    self._event_emitter.emit("output:saved", {"path": str(output_path)})
                except Exception as e:
                    logger.error(f"Failed to save output: {e}")

            return final_result

        except Exception as e:
            self._event_emitter.emit("council:error", {"error": str(e)})
            raise

    def run(self, task: str) -> dict[str, Any]:
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

    def add_step(self, step: Step) -> None:
        """Add a step to the council workflow.

        Args:
            step: The step to add
        """
        self.steps.append(step)

    def _get_agent_names(self) -> list[str]:
        """Get names of all agents in the council."""
        agent_names = []
        for step in self.steps:
            if hasattr(step, "agents"):
                for agent in step.agents:
                    if hasattr(agent, "name"):
                        agent_names.append(agent.name)
                    else:
                        agent_names.append(str(agent))
        return list(set(agent_names))  # Remove duplicates

    def handle_error(self, error: Exception, context: Context) -> None:
        """Handle errors according to the configured strategy.

        Args:
            error: The exception that occurred
            context: Current council context
        """
        logger.error(f"Council error: {error}")
        self._event_emitter.emit(
            "council:error",
            {
                "error": str(error),
                "strategy": self.error_strategy,
                "context_summary": context.get_summary(),
            },
        )
