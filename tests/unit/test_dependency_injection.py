"""Tests for dependency injection in Council."""

import pytest

from konseho.adapters import MockAgent, MockEventEmitter, MockOutputManager
from konseho.core.context import Context
from konseho.core.council import Council
from konseho.core.output_manager import OutputManager
from konseho.execution.events import EventEmitter
from konseho.factories import CouncilDependencies, CouncilFactory
from konseho.protocols import IContext, IEventEmitter, IOutputManager


class TestCouncilDependencyInjection:
    """Test dependency injection in Council class."""

    def test_council_requires_dependencies(self):
        """Test that Council requires dependencies."""
        # Create council without dependencies parameter should fail
        with pytest.raises(ValueError, match="Council requires dependencies"):
            Council(name="test_council", agents=[MockAgent("test")])

    def test_dependency_injection_overrides_defaults(self):
        """Test that injected dependencies override defaults."""
        # Create custom dependencies
        mock_context = Context({"injected": True})
        mock_emitter = MockEventEmitter()
        mock_output = MockOutputManager()

        deps = CouncilDependencies(
            context=mock_context, event_emitter=mock_emitter, output_manager=mock_output
        )

        # Create council with dependencies
        council = Council(
            name="injected_council",
            dependencies=deps,
            save_outputs=True,  # Should be ignored when deps provided
        )

        # Verify injected dependencies are used
        assert council.context is mock_context
        assert council._event_emitter is mock_emitter
        assert council.output_manager is mock_output

    def test_dependencies_implement_protocols(self):
        """Test that all dependencies implement their protocols."""
        # Default dependencies
        context = Context()
        emitter = EventEmitter()
        output = OutputManager("test")

        # Verify protocol implementation
        assert isinstance(context, IContext)
        assert isinstance(emitter, IEventEmitter)
        assert isinstance(output, IOutputManager)

        # Mock dependencies
        mock_context = Context()
        mock_emitter = MockEventEmitter()
        mock_output = MockOutputManager()

        # Verify mock protocol implementation
        assert isinstance(mock_context, IContext)
        assert isinstance(mock_emitter, IEventEmitter)
        assert isinstance(mock_output, IOutputManager)

    @pytest.mark.asyncio
    async def test_mock_event_emitter_captures_events(self):
        """Test that MockEventEmitter properly captures events."""
        mock_emitter = MockEventEmitter()

        # Create council with mock emitter
        deps = CouncilDependencies(event_emitter=mock_emitter)
        council = Council(
            name="test",
            agents=[MockAgent("agent1", response="response1")],
            dependencies=deps,
        )

        # Execute council
        await council.execute("test task")

        # Verify events were captured
        events = mock_emitter.get_emitted_events()
        event_types = [event for event, _ in events]

        assert "council:start" in event_types
        assert "step:start" in event_types
        assert "step:complete" in event_types
        assert "council:complete" in event_types

    @pytest.mark.asyncio
    async def test_mock_output_manager_saves_outputs(self):
        """Test that MockOutputManager properly saves outputs."""
        mock_output = MockOutputManager()

        # Create council with mock output manager
        deps = CouncilDependencies(output_manager=mock_output)
        council = Council(
            name="test",
            agents=[MockAgent("agent1")],
            dependencies=deps,
            save_outputs=True,
        )

        # Execute council
        await council.execute("test task")

        # Verify outputs were saved
        saved = mock_output.get_saved_outputs()
        assert len(saved) == 1
        assert saved[0]["task"] == "test task"
        assert saved[0]["council_name"] == "test"


class TestCouncilFactory:
    """Test the CouncilFactory pattern."""

    def test_factory_creates_council_with_defaults(self):
        """Test factory creates council with default dependencies."""
        factory = CouncilFactory()

        council = factory.create_council(
            name="factory_council", agents=[MockAgent("test")]
        )

        assert council.name == "factory_council"
        assert isinstance(council.context, IContext)
        assert isinstance(council._event_emitter, IEventEmitter)

    def test_factory_with_custom_dependencies(self):
        """Test factory with custom dependencies."""
        custom_deps = CouncilDependencies(
            context=Context({"custom": True}),
            event_emitter=MockEventEmitter(),
            output_manager=MockOutputManager(),
        )

        factory = CouncilFactory(dependencies=custom_deps)
        council = factory.create_council(name="custom")

        assert council.context.get("custom") is True
        assert isinstance(council._event_emitter, MockEventEmitter)
        assert isinstance(council.output_manager, MockOutputManager)

    def test_factory_create_test_council(self):
        """Test factory creates test council with mocks."""
        factory = CouncilFactory()

        mock_context = Context()
        mock_emitter = MockEventEmitter()
        mock_output = MockOutputManager()

        test_council = factory.create_test_council(
            name="test",
            mock_context=mock_context,
            mock_event_emitter=mock_emitter,
            mock_output_manager=mock_output,
        )

        assert test_council.name == "test"
        assert test_council.context is mock_context
        assert test_council._event_emitter is mock_emitter
        assert test_council.output_manager is mock_output

    def test_factory_handles_output_manager_creation(self):
        """Test factory creates output manager when needed."""
        factory = CouncilFactory()

        # Without save_outputs
        council1 = factory.create_council(name="no_output", save_outputs=False)
        assert council1.output_manager is None

        # With save_outputs and output_dir
        council2 = factory.create_council(
            name="with_output", save_outputs=True, output_dir="test_outputs"
        )
        # Should create output manager
        assert council2.output_manager is not None


class TestCouncilDependencies:
    """Test the CouncilDependencies container."""

    def test_dependencies_default_initialization(self):
        """Test dependencies container creates defaults."""
        deps = CouncilDependencies()

        assert isinstance(deps.context, Context)
        assert isinstance(deps.event_emitter, EventEmitter)
        assert deps.output_manager is None

    def test_dependencies_with_output_manager(self):
        """Test creating dependencies with output manager."""
        deps = CouncilDependencies.with_output_manager(output_dir="test_dir")

        assert isinstance(deps.context, Context)
        assert isinstance(deps.event_emitter, EventEmitter)
        assert isinstance(deps.output_manager, OutputManager)

    def test_dependencies_partial_override(self):
        """Test partial override of dependencies."""
        custom_context = Context({"custom": True})

        deps = CouncilDependencies(context=custom_context)

        assert deps.context is custom_context
        assert isinstance(deps.event_emitter, EventEmitter)  # Default
        assert deps.output_manager is None  # Default


class TestMockImplementations:
    """Test the mock implementations for testing."""

    def test_mock_event_emitter_handlers(self):
        """Test MockEventEmitter handler registration."""
        emitter = MockEventEmitter()

        called = []

        def handler(event, data):
            called.append((event, data))

        emitter.on("test", handler)
        emitter.emit("test", {"data": "value"})

        assert len(called) == 1
        assert called[0] == ("test", {"data": "value"})

    @pytest.mark.asyncio
    async def test_mock_event_emitter_async(self):
        """Test MockEventEmitter async support."""
        emitter = MockEventEmitter()

        called = []

        async def async_handler(event, data):
            called.append((event, data))

        emitter.on("test", async_handler)
        await emitter.emit_async("test", {"async": True})

        assert len(called) == 1
        assert called[0] == ("test", {"async": True})

    def test_mock_output_manager_operations(self):
        """Test MockOutputManager operations."""
        manager = MockOutputManager()

        # Save outputs
        path1 = manager.save_formatted_output("task1", {"result": 1})
        path2 = manager.save_formatted_output("task2", {"result": 2})

        assert "/mock/outputs/" in path1
        assert len(manager.saved_outputs) == 2

        # Clean outputs
        cleaned = manager.clean_old_outputs()
        assert cleaned == 1
        assert len(manager.saved_outputs) == 1
