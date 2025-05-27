"""Adapter classes for migrating to protocol-based architecture.

These adapters help bridge the gap between existing implementations
and the new protocol interfaces, allowing for gradual migration.
"""

import asyncio
from typing import Any

from konseho.agents.base import AgentWrapper
from konseho.core.context import Context
from konseho.core.steps import Step, StepResult
from konseho.protocols import (
    IAgent,
    IContext,
    IStep,
    IStepResult,
)


class AgentAdapter(IAgent):
    """Adapt existing AgentWrapper to IAgent protocol."""

    def __init__(self, agent: AgentWrapper):
        """Initialize adapter with existing agent.

        Args:
            agent: Existing AgentWrapper instance
        """
        self._agent = agent

    @property
    def name(self) -> str:
        """Agent's unique name."""
        return self._agent.name

    @property
    def model(self) -> str:
        """Model identifier."""
        # AgentWrapper might not have model attribute directly
        return getattr(self._agent, "model", "unknown")

    async def work_on(self, task: str) -> str:
        """Process a task and return result."""
        return await self._agent.work_on(task)

    def get_capabilities(self) -> dict[str, Any]:
        """Return agent capabilities."""
        # Extract capabilities from the wrapped agent
        capabilities = {}
        if hasattr(self._agent, "_strands_agent"):
            strands_agent = self._agent._strands_agent
            if hasattr(strands_agent, "tools"):
                capabilities["tools"] = [t.name for t in strands_agent.tools]
            if hasattr(strands_agent, "model"):
                capabilities["model"] = strands_agent.model
        return capabilities


class StepAdapter(IStep):
    """Adapt existing Step to IStep protocol."""

    def __init__(self, step: Step):
        """Initialize adapter with existing step.

        Args:
            step: Existing Step instance
        """
        self._step = step

    @property
    def name(self) -> str:
        """Step name."""
        return self._step.name

    async def execute(self, task: str, context: IContext) -> IStepResult:
        """Execute the step."""
        # The existing Step class expects a Context instance
        if isinstance(context, Context):
            result = await self._step.execute(task, context)
        else:
            # Convert IContext to Context if needed
            ctx = Context()
            ctx._data = context.to_dict()
            result = await self._step.execute(task, ctx)

        # Wrap result if needed
        if isinstance(result, StepResult):
            return StepResultAdapter(result)
        return result

    def validate(self) -> list[str]:
        """Validate step configuration."""
        # Existing steps might not have validate method
        if hasattr(self._step, "validate"):
            return self._step.validate()
        return []


class StepResultAdapter(IStepResult):
    """Adapt existing StepResult to IStepResult protocol."""

    def __init__(self, result: StepResult):
        """Initialize adapter with existing result.

        Args:
            result: Existing StepResult instance
        """
        self._result = result

    @property
    def output(self) -> str:
        """Main output from the step."""
        return self._result.output

    @property
    def metadata(self) -> dict[str, Any]:
        """Additional metadata."""
        return self._result.metadata

    @property
    def success(self) -> bool:
        """Whether the step executed successfully."""
        # Add success property if not present
        return getattr(self._result, "success", True)


class ContextAdapter(IContext):
    """Adapt existing Context to IContext protocol."""

    def __init__(self, context: Context):
        """Initialize adapter with existing context.

        Args:
            context: Existing Context instance
        """
        self._context = context

    def add(self, key: str, value: Any) -> None:
        """Add a key-value pair to context."""
        self._context.add(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context."""
        return self._context.get(key, default)

    def update(self, data: dict[str, Any]) -> None:
        """Update context with multiple key-value pairs."""
        self._context.update(data)

    def to_dict(self) -> dict[str, Any]:
        """Export context as dictionary."""
        return self._context.to_dict()

    def get_size(self) -> int:
        """Get context size."""
        # Existing Context might not have get_size
        if hasattr(self._context, "get_size"):
            return self._context.get_size()
        # Estimate size from string representation
        import sys

        return sys.getsizeof(str(self._context.to_dict()))

    def clear(self) -> None:
        """Clear all context data."""
        if hasattr(self._context, "clear"):
            self._context.clear()
        else:
            self._context._data.clear()


class MockAgent(IAgent):
    """Mock agent for testing purposes."""

    def __init__(self, name: str, model: str = "mock", response: str = "Mock response"):
        """Initialize mock agent.

        Args:
            name: Agent name
            model: Model identifier
            response: Fixed response to return
        """
        self._name = name
        self._model = model
        self._response = response
        self._capabilities = {"mock": True}

    @property
    def name(self) -> str:
        """Agent's unique name."""
        return self._name

    @property
    def model(self) -> str:
        """Model identifier."""
        return self._model

    async def work_on(self, task: str) -> str:
        """Process a task and return mock response."""
        return self._response

    def get_capabilities(self) -> dict[str, Any]:
        """Return mock capabilities."""
        return self._capabilities


class MockStep(IStep):
    """Mock step for testing purposes."""

    def __init__(self, name: str, output: str = "Mock output"):
        """Initialize mock step.

        Args:
            name: Step name
            output: Fixed output to return
        """
        self._name = name
        self._output = output

    @property
    def name(self) -> str:
        """Step name."""
        return self._name

    async def execute(self, task: str, context: IContext) -> IStepResult:
        """Execute mock step."""
        return MockStepResult(self._output)

    def validate(self) -> list[str]:
        """No validation errors for mock."""
        return []


class MockStepResult(IStepResult):
    """Mock step result for testing."""

    def __init__(self, output: str, success: bool = True):
        """Initialize mock result.

        Args:
            output: Result output
            success: Whether execution succeeded
        """
        self._output = output
        self._success = success
        self._metadata = {"mock": True}

    @property
    def output(self) -> str:
        """Main output."""
        return self._output

    @property
    def metadata(self) -> dict[str, Any]:
        """Metadata."""
        return self._metadata

    @property
    def success(self) -> bool:
        """Success status."""
        return self._success


class MockEventEmitter:
    """Mock event emitter for testing."""

    def __init__(self):
        """Initialize mock event emitter."""
        self.events: list[tuple[str, Any]] = []
        self.handlers: dict[str, list[Any]] = {}

    def on(self, event: str, handler: Any) -> None:
        """Register an event handler."""
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)

    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event and record it."""
        self.events.append((event, data))
        # Call handlers for testing
        if event in self.handlers:
            for handler in self.handlers[event]:
                handler(event, data)

    async def emit_async(self, event: str, data: Any = None) -> None:
        """Emit an event asynchronously."""
        self.events.append((event, data))
        # Call handlers for testing
        if event in self.handlers:
            for handler in self.handlers[event]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, data)
                else:
                    handler(event, data)

    def get_emitted_events(self) -> list[tuple[str, Any]]:
        """Get all emitted events for verification."""
        return self.events

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()


class MockOutputManager:
    """Mock output manager for testing."""

    def __init__(self):
        """Initialize mock output manager."""
        self.saved_outputs: list[dict[str, Any]] = []

    def save_formatted_output(
        self,
        task: str,
        result: Any,
        council_name: str = "council",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Mock save output and return fake path."""
        self.saved_outputs.append(
            {
                "task": task,
                "result": result,
                "council_name": council_name,
                "metadata": metadata,
            }
        )
        return f"/mock/outputs/{council_name}_{len(self.saved_outputs)}.json"

    def clean_old_outputs(self, max_age_days: int = 7) -> int:
        """Mock clean old outputs."""
        # Simulate cleaning half the outputs
        cleaned = len(self.saved_outputs) // 2
        if cleaned > 0:
            self.saved_outputs = self.saved_outputs[cleaned:]
        return cleaned

    def get_saved_outputs(self) -> list[dict[str, Any]]:
        """Get all saved outputs for verification."""
        return self.saved_outputs
