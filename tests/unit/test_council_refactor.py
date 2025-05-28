"""Tests for the refactored Council class and its components."""


import pytest

from konseho.adapters import MockAgent, MockEventEmitter, MockOutputManager, MockStep
from konseho.core import (
    Council,
    ErrorHandler,
    ErrorStrategy,
    ModeratorAssigner,
    StepOrchestrator,
)
from konseho.core.context import Context
from konseho.core.steps import DebateStep, StepResult
from konseho.factories import CouncilDependencies, CouncilFactory


class TestErrorHandler:
    """Tests for ErrorHandler component."""

    @pytest.mark.asyncio
    async def test_halt_strategy(self):
        """Test that halt strategy re-raises errors."""
        handler = ErrorHandler(error_strategy=ErrorStrategy.HALT)

        error = ValueError("Test error")
        step = MockStep("test_step")

        with pytest.raises(ValueError, match="Test error"):
            await handler.handle_step_error(error, step, "task", Context())

    @pytest.mark.asyncio
    async def test_continue_strategy(self):
        """Test that continue strategy returns error result."""
        handler = ErrorHandler(error_strategy=ErrorStrategy.CONTINUE)

        error = ValueError("Test error")
        step = MockStep("test_step")

        result = await handler.handle_step_error(error, step, "task", Context())

        assert isinstance(result, StepResult)
        assert result.metadata["step_name"] == "test_step"
        assert "Test error" in result.output
        assert result.metadata["error"] == "Test error"
        assert result.metadata["skipped"] is True

    @pytest.mark.asyncio
    async def test_retry_strategy(self):
        """Test retry strategy with max retries."""
        handler = ErrorHandler(error_strategy=ErrorStrategy.RETRY, max_retries=2)

        error = ValueError("Test error")
        step = MockStep("test_step")

        # First retry - should return None to signal retry
        result = await handler.handle_step_error(
            error, step, "task", Context(), attempt=0
        )
        assert result is None

        # Second retry - should still return None
        result = await handler.handle_step_error(
            error, step, "task", Context(), attempt=1
        )
        assert result is None

        # Max retries exceeded - should raise
        with pytest.raises(ValueError, match="Test error"):
            await handler.handle_step_error(error, step, "task", Context(), attempt=2)

    @pytest.mark.asyncio
    async def test_fallback_strategy_with_handler(self):
        """Test fallback strategy with custom handler."""

        async def fallback_handler(error, step, task, context):
            return StepResult(
                output=f"Fallback handled: {error}",
                metadata={
                    "fallback": True,
                    "step_name": step.name,
                    "agents_involved": [],
                },
            )

        handler = ErrorHandler(
            error_strategy=ErrorStrategy.FALLBACK, fallback_handler=fallback_handler
        )

        error = ValueError("Test error")
        step = MockStep("test_step")

        result = await handler.handle_step_error(error, step, "task", Context())

        assert isinstance(result, StepResult)
        assert "Fallback handled" in result.output
        assert result.metadata["fallback"] is True

    @pytest.mark.asyncio
    async def test_execute_with_error_handling_success(self):
        """Test execute wrapper with successful execution."""
        handler = ErrorHandler()

        async def mock_execute(step, task, context):
            return StepResult(
                output="Success",
                metadata={"step_name": step.name, "agents_involved": []},
            )

        step = MockStep("test_step")
        result = await handler.execute_with_error_handling(
            step, "task", Context(), mock_execute
        )

        assert result.output == "Success"

    @pytest.mark.asyncio
    async def test_execute_with_error_handling_retry(self):
        """Test execute wrapper with retry logic."""
        handler = ErrorHandler(error_strategy=ErrorStrategy.RETRY, max_retries=2)

        call_count = 0

        async def mock_execute(step, task, context):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Retry me")
            return StepResult(
                output="Success after retries",
                metadata={"step_name": step.name, "agents_involved": []},
            )

        step = MockStep("test_step")
        result = await handler.execute_with_error_handling(
            step, "task", Context(), mock_execute
        )

        assert call_count == 3
        assert result.output == "Success after retries"


class TestStepOrchestrator:
    """Tests for StepOrchestrator component."""

    @pytest.mark.asyncio
    async def test_execute_steps_success(self):
        """Test successful execution of multiple steps."""
        step1 = MockStep("step1", output="Result 1")
        step2 = MockStep("step2", output="Result 2")

        event_emitter = MockEventEmitter()
        orchestrator = StepOrchestrator(
            steps=[step1, step2], event_emitter=event_emitter
        )

        context = Context()
        results = await orchestrator.execute_steps("test task", context)

        assert len(results) == 2
        assert results[0].output == "Result 1"
        assert results[1].output == "Result 2"

        # Check events were emitted
        assert any(e[0] == "council_started" for e in event_emitter.events)
        assert any(e[0] == "step_started" for e in event_emitter.events)
        assert any(e[0] == "step_completed" for e in event_emitter.events)
        assert any(e[0] == "council_completed" for e in event_emitter.events)

    @pytest.mark.asyncio
    async def test_execute_steps_with_context_updates(self):
        """Test that context is updated after each step."""
        step1 = MockStep("step1", output="Result 1")
        step2 = MockStep("step2", output="Result 2")

        orchestrator = StepOrchestrator(steps=[step1, step2])

        context = Context()
        results = await orchestrator.execute_steps("test task", context)

        # Check context was updated
        results_dict = context.get_results()
        assert len(results_dict) == 2
        assert results_dict["step_0"].output == "Result 1"
        assert results_dict["step_1"].output == "Result 2"

    @pytest.mark.asyncio
    async def test_execute_steps_with_event_emission(self):
        """Test that events are emitted during execution."""
        step1 = MockStep("step1", output="Result 1")

        event_emitter = MockEventEmitter()
        orchestrator = StepOrchestrator(steps=[step1], event_emitter=event_emitter)

        context = Context()
        await orchestrator.execute_steps("test task", context)

        # Check events were emitted
        event_types = [e[0] for e in event_emitter.events]
        assert "council_started" in event_types
        assert "step_started" in event_types
        assert "step_completed" in event_types
        assert "council_completed" in event_types


class TestModeratorAssigner:
    """Tests for ModeratorAssigner component."""

    def test_assign_moderators_with_pool(self):
        """Test assigning moderators from a pool."""
        agent1 = MockAgent("moderator1")
        agent2 = MockAgent("moderator2")
        agent3 = MockAgent("debater1")
        agent4 = MockAgent("debater2")

        debate_step1 = DebateStep([agent3, agent4])
        debate_step2 = DebateStep([agent3, agent4])

        assigner = ModeratorAssigner()
        assigner.set_moderator_pool([agent1, agent2])

        assigner.assign_moderators([debate_step1, debate_step2])

        # Should round-robin through the pool
        assert debate_step1.moderator == agent1
        assert debate_step2.moderator == agent2

    def test_assign_moderators_with_default(self):
        """Test assigning default moderator."""
        default_mod = MockAgent("default_moderator")
        agent1 = MockAgent("debater1")
        agent2 = MockAgent("debater2")

        debate_step = DebateStep([agent1, agent2])

        assigner = ModeratorAssigner(default_moderator=default_mod)
        assigner.assign_moderators([debate_step])

        assert debate_step.moderator == default_mod

    def test_assign_specific_moderator(self):
        """Test assigning a specific moderator to a step."""
        moderator = MockAgent("specific_moderator")
        agent1 = MockAgent("debater1")
        agent2 = MockAgent("debater2")

        debate_step = DebateStep([agent1, agent2])

        assigner = ModeratorAssigner()
        assigner.assign_specific_moderator(debate_step, moderator)

        assert debate_step.moderator == moderator

    def test_skip_non_debate_steps(self):
        """Test that non-debate steps are skipped."""
        regular_step = MockStep("regular")

        assigner = ModeratorAssigner()
        # Should not raise any errors
        assigner.assign_moderators([regular_step])


class TestCouncilRefactored:
    """Tests for the refactored Council class."""

    def test_council_requires_dependencies(self):
        """Test that Council requires dependencies."""
        with pytest.raises(ValueError, match="Council requires dependencies"):
            Council(name="test")

    @pytest.mark.asyncio
    async def test_council_with_factory(self):
        """Test creating Council with factory."""
        factory = CouncilFactory()
        council = factory.create_council(
            name="test_council", steps=[MockStep("step1", output="Test output")]
        )

        result = await council.execute("test task")

        assert result["council"] == "test_council"
        assert result["task"] == "test task"
        assert result["steps_completed"] == 1

    @pytest.mark.asyncio
    async def test_council_with_custom_dependencies(self):
        """Test creating Council with custom dependencies."""
        event_emitter = MockEventEmitter()
        output_manager = MockOutputManager()

        deps = CouncilDependencies(
            event_emitter=event_emitter, output_manager=output_manager
        )

        council = Council(
            name="test_council",
            steps=[MockStep("step1", output="Test output")],
            dependencies=deps,
        )

        result = await council.execute("test task")

        # Check events were emitted
        assert len(event_emitter.events) > 0

        # Check output was saved
        assert len(output_manager.outputs) > 0

    @pytest.mark.asyncio
    async def test_council_error_strategies(self):
        """Test Council with different error strategies."""
        # Test continue strategy
        deps = CouncilDependencies()
        council = Council(
            name="test_council",
            steps=[MockStep("failing_step", should_fail=True)],
            dependencies=deps,
            error_strategy="continue",
        )

        result = await council.execute("test task")
        assert result["steps_completed"] == 1

    def test_add_step(self):
        """Test adding steps to council."""
        deps = CouncilDependencies()
        council = Council(name="test", dependencies=deps)

        step = MockStep("new_step")
        council.add_step(step)

        assert len(council.steps) == 1
        assert council.steps[0] == step
        assert len(council._step_orchestrator.steps) == 1

    def test_set_moderator_pool(self):
        """Test setting moderator pool."""
        agent1 = MockAgent("mod1")
        agent2 = MockAgent("mod2")
        agent3 = MockAgent("debater1")
        agent4 = MockAgent("debater2")

        deps = CouncilDependencies()
        council = Council(
            name="test", steps=[DebateStep([agent3, agent4])], dependencies=deps
        )

        council.set_moderator_pool([agent1, agent2])

        # Check that moderator was assigned
        debate_step = council.steps[0]
        assert debate_step.moderator in [agent1, agent2]

    def test_run_sync_wrapper(self):
        """Test synchronous run method."""
        deps = CouncilDependencies()
        council = Council(
            name="test",
            steps=[MockStep("step1", output="Sync result")],
            dependencies=deps,
        )

        result = council.run("test task")

        assert result["council"] == "test"
        assert result["steps_completed"] == 1
