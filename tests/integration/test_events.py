"""Integration tests for event system."""

import asyncio
from typing import Any

import pytest

from konseho import (
    AgentWrapper,
    DebateStep,
    EventEmitter,
    ParallelStep,
)
from konseho.factories import CouncilFactory
from tests.fixtures import EventCollector, MockStrandsAgent


class TestEventSystem:
    """Test event emission and handling."""

    @pytest.mark.asyncio
    async def test_council_lifecycle_events(self):
        """Test all council lifecycle events are emitted."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        factory = CouncilFactory()
        council = factory.create_council("test", [ParallelStep([agent])])

        collector = EventCollector()

        # Subscribe to all events
        events = [
            "council_started",
            "council_completed",
            "council_error",
            "step_started",
            "step_completed",
            "step_error",
        ]

        for event in events:
            council._event_emitter.on(event, collector.collect)

        await council.execute("Test task")

        # Verify expected events
        sequence = collector.get_event_sequence()
        assert sequence == [
            "council_started",
            "step_started",
            "step_completed",
            "council_completed",
        ]

        # Verify event data
        start_event = collector.get_events_by_type("council_started")[0]
        assert start_event.data["council"] == "test"
        assert start_event.data["task"] == "Test task"

    @pytest.mark.asyncio
    async def test_step_error_events(self):
        """Test error events are properly emitted."""

        class FailingStep:
            name = "FailingStep"

            def validate(self):
                """Validation method required by Step interface."""
                pass

            async def execute(self, task, context):
                raise ValueError("Step failed")

        factory = CouncilFactory()
        council = factory.create_council(
            "test", [FailingStep()], error_strategy="continue"
        )

        collector = EventCollector()
        council._event_emitter.on("step_error", collector.collect)
        council._event_emitter.on("council_completed", collector.collect)

        await council.execute("Test")

        # Should have step error but council still completes
        assert collector.has_event("step_error")
        assert collector.has_event("council_completed")

        error_event = collector.get_events_by_type("step_error")[0]
        assert "Step failed" in error_event.data["error"]

    @pytest.mark.asyncio
    async def test_async_event_handlers(self):
        """Test async event handlers work correctly."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        factory = CouncilFactory()
        council = factory.create_council("test", [ParallelStep([agent])])

        async_events = []

        async def async_handler(event_type: str, data: dict[str, Any]):
            await asyncio.sleep(0.01)  # Simulate async work
            async_events.append((event_type, data))

        council._event_emitter.on("council_started", async_handler)
        council._event_emitter.on("council_completed", async_handler)

        await council.execute("Test")

        # Give async handlers time to complete
        await asyncio.sleep(0.05)

        assert len(async_events) == 2
        assert async_events[0][0] == "council_started"
        assert async_events[1][0] == "council_completed"

    @pytest.mark.asyncio
    async def test_event_handler_errors(self):
        """Test council continues even if event handler fails."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        factory = CouncilFactory()
        council = factory.create_council("test", [ParallelStep([agent])])

        def failing_handler(event_type: str, data: dict[str, Any]):
            raise RuntimeError("Handler failed")

        def good_handler(event_type: str, data: dict[str, Any]):
            good_handler.called = True

        good_handler.called = False

        council._event_emitter.on("council_started", failing_handler)
        council._event_emitter.on("council_started", good_handler)

        # Should not raise despite handler error
        await council.execute("Test")

        # Good handler should still be called
        assert good_handler.called

    @pytest.mark.asyncio
    async def test_event_data_integrity(self):
        """Test event data contains expected information."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))

        step1 = ParallelStep([agent1])
        step2 = DebateStep([agent1, agent2])

        factory = CouncilFactory()
        council = factory.create_council("test", [step1, step2])

        collector = EventCollector()
        council._event_emitter.on("step_started", collector.collect)
        council._event_emitter.on("step_completed", collector.collect)

        await council.execute("Test task")

        # Check step start events
        start_events = collector.get_events_by_type("step_started")
        assert len(start_events) == 2

        assert start_events[0].data["step"] == 0
        assert start_events[0].data["type"] == "ParallelStep"

        assert start_events[1].data["step"] == 1
        assert start_events[1].data["type"] == "DebateStep"

        # Check step complete events
        complete_events = collector.get_events_by_type("step_completed")
        assert len(complete_events) == 2

        for event in complete_events:
            assert "result" in event.data

    @pytest.mark.asyncio
    async def test_event_emitter_subscription_management(self):
        """Test adding and removing event handlers."""
        emitter = EventEmitter()

        handler1_calls = []
        handler2_calls = []

        def handler1(event_type, data):
            handler1_calls.append(event_type)

        def handler2(event_type, data):
            handler2_calls.append(event_type)

        # Add handlers
        emitter.on("test", handler1)
        emitter.on("test", handler2)

        emitter.emit("test", {})
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

        # Remove one handler
        emitter.off("test", handler1)

        emitter.emit("test", {})
        assert len(handler1_calls) == 1  # No new calls
        assert len(handler2_calls) == 2  # Still active

    @pytest.mark.asyncio
    async def test_multiple_councils_event_isolation(self):
        """Test events from different councils don't interfere."""
        agent = AgentWrapper(MockStrandsAgent("agent"))

        # Create separate factories to ensure separate event emitters
        factory1 = CouncilFactory()
        council1 = factory1.create_council("council1", [ParallelStep([agent])])

        factory2 = CouncilFactory()
        council2 = factory2.create_council("council2", [ParallelStep([agent])])

        collector1 = EventCollector()
        collector2 = EventCollector()

        council1._event_emitter.on("council_started", collector1.collect)
        council2._event_emitter.on("council_started", collector2.collect)

        # Execute both councils
        await asyncio.gather(council1.execute("Task 1"), council2.execute("Task 2"))

        # Each should have only its own events
        assert len(collector1.events) == 1
        assert collector1.events[0].data["council"] == "council1"

        assert len(collector2.events) == 1
        assert collector2.events[0].data["council"] == "council2"

    @pytest.mark.asyncio
    async def test_event_timing_and_order(self):
        """Test events are emitted at correct times."""
        agent = AgentWrapper(MockStrandsAgent("agent", delay=0.1))
        factory = CouncilFactory()
        council = factory.create_council("test", [ParallelStep([agent])])

        event_times = []

        def time_handler(event_type, data):
            import time

            event_times.append((event_type, time.time()))

        council._event_emitter.on("council_started", time_handler)
        council._event_emitter.on("step_started", time_handler)
        council._event_emitter.on("step_completed", time_handler)
        council._event_emitter.on("council_completed", time_handler)

        await council.execute("Test")

        # Verify chronological order
        for i in range(len(event_times) - 1):
            assert event_times[i][1] <= event_times[i + 1][1]

        # Step should take at least the agent delay
        step_start = next(t for e, t in event_times if e == "step_started")
        step_end = next(t for e, t in event_times if e == "step_completed")
        assert step_end - step_start >= 0.09  # Allow small variance
