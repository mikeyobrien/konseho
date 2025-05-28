"""Unit tests for execution engine."""

import asyncio
from typing import Any

import pytest

from konseho.core.context import Context
from konseho.core.steps import Step
from konseho.execution.events import CouncilEvent, EventEmitter, EventType
from konseho.execution.executor import AsyncExecutor, StepExecutor


class TestStepExecutor:
    """Tests for StepExecutor async execution."""

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self):
        """Verify agents execute in parallel, not sequentially."""
        execution_times = []

        class TimedAgent:
            def __init__(self, name: str, delay: float):
                self.name = name
                self.delay = delay

            async def work_on(self, task: str) -> str:
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(self.delay)
                execution_times.append((self.name, start))
                return f"{self.name} completed"

        agents = [TimedAgent("fast", 0.1), TimedAgent("slow", 0.2)]

        executor = StepExecutor()
        context = Context()

        start = asyncio.get_event_loop().time()
        results = await executor.execute_parallel(agents, "test task", context)
        total_time = asyncio.get_event_loop().time() - start

        # Should complete in ~0.2s (parallel) not 0.3s (sequential)
        assert total_time < 0.25, f"Took {total_time}s, should be parallel"
        assert len(results) == 2
        assert results[0] == "fast completed"
        assert results[1] == "slow completed"

        # Verify both started at approximately the same time
        assert abs(execution_times[0][1] - execution_times[1][1]) < 0.01

    @pytest.mark.asyncio
    async def test_event_ordering(self):
        """Events from parallel execution maintain correct order."""
        events = []

        def event_handler(event_type: str, data: dict[str, Any]):
            events.append((event_type, data))

        class MockAgent:
            def __init__(self, name: str):
                self.name = name

            async def work_on(self, task: str) -> str:
                return f"{self.name} result"

        agents = [MockAgent("agent1"), MockAgent("agent2")]

        executor = StepExecutor(event_handler=event_handler)
        context = Context()

        await executor.execute_parallel(agents, "test", context)

        # Verify event sequence
        event_types = [e[0] for e in events]
        assert event_types[0] == "parallel:start"
        assert "agent:start" in event_types
        assert "agent:complete" in event_types
        assert event_types[-1] == "parallel:complete"

    @pytest.mark.asyncio
    async def test_error_handling_halt_strategy(self):
        """Test halt strategy stops on first error."""

        class FailingAgent:
            async def work_on(self, task: str) -> str:
                raise ValueError("Agent failed")

        class GoodAgent:
            async def work_on(self, task: str) -> str:
                return "success"

        agents = [GoodAgent(), FailingAgent()]
        executor = StepExecutor(error_strategy="halt")
        context = Context()

        with pytest.raises(ValueError, match="Agent failed"):
            await executor.execute_parallel(agents, "test", context)

    @pytest.mark.asyncio
    async def test_error_handling_continue_strategy(self):
        """Test continue strategy collects partial results."""

        class FailingAgent:
            async def work_on(self, task: str) -> str:
                raise ValueError("Agent failed")

        class GoodAgent:
            async def work_on(self, task: str) -> str:
                return "success"

        agents = [GoodAgent(), FailingAgent()]
        executor = StepExecutor(error_strategy="continue")
        context = Context()

        results = await executor.execute_parallel(agents, "test", context)

        # Should have one success and one error
        assert len(results) == 2
        assert results[0] == "success"
        assert isinstance(results[1], Exception)

    @pytest.mark.asyncio
    async def test_error_handling_retry_strategy(self):
        """Test retry strategy attempts multiple times."""
        call_count = 0

        class RetryAgent:
            async def work_on(self, task: str) -> str:
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ValueError(f"Attempt {call_count} failed")
                return "success after retries"

        agents = [RetryAgent()]
        executor = StepExecutor(error_strategy="retry", retry_attempts=3)
        context = Context()

        results = await executor.execute_parallel(agents, "test", context)

        assert call_count == 3
        assert results[0] == "success after retries"

    @pytest.mark.asyncio
    async def test_context_injection(self):
        """Test agents receive context in their prompts."""
        received_tasks = []

        class ContextAgent:
            async def work_on(self, task: str) -> str:
                received_tasks.append(task)
                return "done"

        agents = [ContextAgent()]
        executor = StepExecutor()
        context = Context({"key": "value"})
        context.add_result("previous", {"data": "previous result"})

        await executor.execute_parallel(agents, "base task", context)

        # Agent should receive task with context
        assert len(received_tasks) == 1
        task_with_context = received_tasks[0]
        assert "base task" in task_with_context
        assert "Current Context:" in task_with_context
        assert "key" in task_with_context
        assert "previous result" in task_with_context


class TestAsyncExecutor:
    """Tests for AsyncExecutor managing multiple councils."""

    @pytest.mark.asyncio
    async def test_concurrency_limit(self):
        """Test executor respects concurrency limits."""
        execution_order = []

        class DelayedStep(Step):
            def __init__(self, name: str, delay: float):
                self.name = name
                self.delay = delay

            async def execute(self, task: str, context: Context):
                execution_order.append(f"{self.name}_start")
                await asyncio.sleep(self.delay)
                execution_order.append(f"{self.name}_end")
                return {"result": f"{self.name} completed"}

        steps = [
            DelayedStep("step1", 0.1),
            DelayedStep("step2", 0.1),
            DelayedStep("step3", 0.1),
            DelayedStep("step4", 0.1),
        ]

        executor = AsyncExecutor(max_concurrent=2)

        start = asyncio.get_event_loop().time()
        results = await executor.execute_steps(steps, "test", Context())
        duration = asyncio.get_event_loop().time() - start

        # With concurrency=2, should take ~0.2s (2 batches) not 0.1s (all parallel)
        assert 0.15 < duration < 0.25
        assert len(results) == 4

        # First two should start together, then next two
        assert execution_order.count("step1_start") == 1
        assert execution_order.count("step2_start") == 1

    @pytest.mark.asyncio
    async def test_step_error_isolation(self):
        """Test errors in one step don't affect others."""

        class FailingStep(Step):
            async def execute(self, task: str, context: Context):
                raise RuntimeError("Step failed")

        class SuccessStep(Step):
            async def execute(self, task: str, context: Context):
                return {"result": "success"}

        steps = [SuccessStep(), FailingStep(), SuccessStep()]
        executor = AsyncExecutor()

        results = await executor.execute_steps(steps, "test", Context())

        assert len(results) == 3
        assert results[0]["result"] == "success"
        assert isinstance(results[1], Exception)
        assert results[2]["result"] == "success"


class TestEventSystem:
    """Tests for event emission and handling."""

    def test_event_emitter_subscription(self):
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

    def test_event_data_structure(self):
        """Test CouncilEvent data structure."""
        event = CouncilEvent(
            type=EventType.STEP_STARTED,
            data={"step": 0, "type": "ParallelStep"},
            metadata={"council": "test"},
        )

        assert event.type == EventType.STEP_STARTED
        assert event.data["step"] == 0
        assert event.metadata["council"] == "test"
        assert hasattr(event, "timestamp")

    @pytest.mark.asyncio
    async def test_async_event_handlers(self):
        """Test async event handlers work correctly."""
        emitter = EventEmitter()
        async_events = []

        async def async_handler(event_type: str, data: dict[str, Any]):
            await asyncio.sleep(0.01)  # Simulate async work
            async_events.append((event_type, data))

        emitter.on("test", async_handler)
        emitter.emit("test", {"key": "value"})

        # Give async handler time to complete
        await asyncio.sleep(0.05)

        assert len(async_events) == 1
        assert async_events[0][0] == "test"
        assert async_events[0][1]["key"] == "value"

    def test_event_handler_error_isolation(self):
        """Test event emitter continues even if handler fails."""
        emitter = EventEmitter()

        def failing_handler(event_type, data):
            raise RuntimeError("Handler failed")

        def good_handler(event_type, data):
            good_handler.called = True

        good_handler.called = False

        emitter.on("test", failing_handler)
        emitter.on("test", good_handler)

        # Should not raise despite handler error
        emitter.emit("test", {})

        # Good handler should still be called
        assert good_handler.called


class TestDecisionProtocols:
    """Tests for voting and consensus mechanisms."""

    @pytest.mark.asyncio
    async def test_majority_voting(self):
        """Test simple majority voting."""
        from konseho.execution.executor import DecisionProtocol

        proposals = {"agent1": "Option A", "agent2": "Option A", "agent3": "Option B"}

        protocol = DecisionProtocol("majority")
        winner = await protocol.decide(proposals)

        assert winner["option"] == "Option A"
        assert winner["votes"] == 2
        assert winner["strategy"] == "majority"

    @pytest.mark.asyncio
    async def test_moderator_decision(self):
        """Test moderator-based decision making."""
        from konseho.execution.executor import DecisionProtocol

        class MockModerator:
            async def work_on(self, task: str) -> str:
                return "Choose Option A - it's better"

        proposals = {"agent1": "Option A", "agent2": "Option B"}

        protocol = DecisionProtocol("moderator", moderator=MockModerator())
        winner = await protocol.decide(proposals)

        assert "Option A" in winner["decision"]
        assert winner["strategy"] == "moderator"

    @pytest.mark.asyncio
    async def test_consensus_threshold(self):
        """Test consensus with threshold."""
        from konseho.execution.executor import DecisionProtocol

        proposals = {
            "agent1": "Option A",
            "agent2": "Option A",
            "agent3": "Option A",
            "agent4": "Option B",
        }

        protocol = DecisionProtocol("consensus", threshold=0.75)
        winner = await protocol.decide(proposals)

        assert winner["option"] == "Option A"
        assert winner["consensus"] == 0.75
        assert winner["strategy"] == "consensus"
