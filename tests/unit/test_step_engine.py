"""Tests for step execution engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from konseho.core.step_engine import StepExecutionEngine
from konseho.core.steps_v2 import StepResult
from konseho.core.error_handler import ErrorHandler, ErrorStrategy


class MockStep:
    """Mock step for testing."""

    def __init__(self, name: str = "MockStep"):
        self._name = name
        self.execute_called = False
        self.validate_called = False

    @property
    def name(self):
        return self._name

    def validate(self):
        self.validate_called = True
        return []  # No errors

    async def execute(self, task, context):
        self.execute_called = True
        return StepResult(output="Mock output", metadata={"task": task})


class MockEventEmitter:
    """Mock event emitter for testing."""

    def __init__(self):
        self.events = []

    async def emit_async(self, event, data):
        self.events.append((event, data))


class TestStepExecutionEngine:
    """Test the step execution engine."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful step execution."""
        # Setup
        error_handler = MagicMock(spec=ErrorHandler)
        error_handler.execute_with_error_handling = AsyncMock(
            return_value=StepResult(output="Success", metadata={})
        )

        event_emitter = MockEventEmitter()
        engine = StepExecutionEngine(error_handler, event_emitter)

        step = MockStep()
        context = MagicMock()

        # Execute
        result = await engine.execute_step(step, "Test task", context)

        # Verify
        assert result.output == "Success"
        assert error_handler.execute_with_error_handling.called

        # Check events
        events = [e[0] for e in event_emitter.events]
        assert "step_start" in events
        assert "step_complete" in events

    @pytest.mark.asyncio
    async def test_execution_with_error(self):
        """Test step execution with error."""
        # Setup
        error_handler = MagicMock(spec=ErrorHandler)
        error_handler.execute_with_error_handling = AsyncMock(
            side_effect=ValueError("Test error")
        )

        event_emitter = MockEventEmitter()
        engine = StepExecutionEngine(error_handler, event_emitter)

        step = MockStep()
        context = MagicMock()

        # Execute and expect error
        with pytest.raises(ValueError, match="Test error"):
            await engine.execute_step(step, "Test task", context)

        # Check events
        events = [e[0] for e in event_emitter.events]
        assert "step_start" in events
        assert "step_failed" in events

    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test step validation error."""
        # Setup
        error_handler = ErrorHandler(ErrorStrategy.HALT)
        event_emitter = MockEventEmitter()
        engine = StepExecutionEngine(error_handler, event_emitter)

        # Create step with validation error
        step = MockStep()
        step.validate = lambda: ["Validation error 1", "Validation error 2"]

        context = MagicMock()

        # Execute and expect validation error
        with pytest.raises(ValueError, match="Step validation failed"):
            await engine.execute_step(step, "Test task", context)

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Test that events are emitted correctly."""
        # Setup
        error_handler = MagicMock(spec=ErrorHandler)
        error_handler.execute_with_error_handling = AsyncMock(
            return_value=StepResult(
                output="A" * 300,  # Long output to test truncation
                metadata={"key": "value"},
            )
        )

        event_emitter = MockEventEmitter()
        engine = StepExecutionEngine(error_handler, event_emitter)

        step = MockStep("TestStep")
        context = MagicMock()

        # Execute
        await engine.execute_step(step, "A very long task description " * 10, context)

        # Check start event
        start_event = next(e for e in event_emitter.events if e[0] == "step_start")
        assert start_event[1]["step"] == "TestStep"
        assert len(start_event[1]["task"]) == 100  # Truncated

        # Check complete event
        complete_event = next(
            e for e in event_emitter.events if e[0] == "step_complete"
        )
        assert complete_event[1]["step"] == "TestStep"
        assert len(complete_event[1]["result"]["output"]) == 200  # Truncated
        assert complete_event[1]["result"]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_no_event_emitter(self):
        """Test execution without event emitter."""
        # Setup
        error_handler = MagicMock(spec=ErrorHandler)
        error_handler.execute_with_error_handling = AsyncMock(
            return_value=StepResult(output="Success")
        )

        # No event emitter
        engine = StepExecutionEngine(error_handler, None)

        step = MockStep()
        context = MagicMock()

        # Execute - should work without emitter
        result = await engine.execute_step(step, "Test task", context)
        assert result.output == "Success"

