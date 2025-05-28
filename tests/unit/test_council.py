"""Unit tests for Council class."""


import pytest

from konseho import AgentWrapper, Context, Council, DebateStep, ParallelStep
from konseho.core.steps import Step
from konseho.factories import CouncilFactory, CouncilDependencies
from tests.fixtures import EventCollector, MockStrandsAgent


class TestCouncil:
    """Tests for Council orchestrator."""
    
    def test_council_initialization(self):
        """Test council initialization with various configurations."""
        # Basic initialization with factory
        factory = CouncilFactory()
        council = factory.create_council(name="test", steps=[])
        assert council.name == "test"
        assert council.steps == []
        assert isinstance(council.context, Context)
        assert council._error_handler.error_strategy.value == "halt"
        
        # With custom context via dependencies
        custom_context = Context({"key": "value"})
        deps = CouncilDependencies(context=custom_context)
        factory_with_deps = CouncilFactory(dependencies=deps)
        council = factory_with_deps.create_council(name="test", steps=[])
        assert council.context is custom_context
        
        # With error strategy
        council = factory.create_council(name="test", steps=[], error_strategy="continue")
        assert council._error_handler.error_strategy.value == "continue"
    
    def test_council_with_steps(self):
        """Test council accepts different step types."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))
        
        parallel_step = ParallelStep([agent1, agent2])
        debate_step = DebateStep([agent1, agent2])
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="multi_step",
            steps=[parallel_step, debate_step]
        )
        
        assert len(council.steps) == 2
        assert isinstance(council.steps[0], ParallelStep)
        assert isinstance(council.steps[1], DebateStep)
    
    @pytest.mark.asyncio
    async def test_council_execution_success(self):
        """Test successful council execution."""
        # Create mock agents
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Response 1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Response 2"))
        
        step = ParallelStep([agent1, agent2])
        factory = CouncilFactory()
        council = factory.create_council(name="test", steps=[step])
        
        result = await council.execute("Test task")
        
        assert "results" in result
        assert "data" in result
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_council_error_halt_strategy(self):
        """Test council halts on error with halt strategy."""
        # Create a failing step
        class FailingStep(Step):
            async def execute(self, task: str, context: Context):
                raise ValueError("Test error")
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="test",
            steps=[FailingStep()],
            error_strategy="halt"
        )
        
        with pytest.raises(ValueError, match="Test error"):
            await council.execute("Test task")
    
    @pytest.mark.asyncio
    async def test_council_error_continue_strategy(self):
        """Test council continues on error with continue strategy."""
        # Create a failing step followed by successful step
        class FailingStep(Step):
            async def execute(self, task: str, context: Context):
                raise ValueError("Test error")
        
        agent = AgentWrapper(MockStrandsAgent("agent", "Success"))
        success_step = ParallelStep([agent])
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="test",
            steps=[FailingStep(), success_step],
            error_strategy="continue"
        )
        
        # Should complete without raising
        result = await council.execute("Test task")
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_council_error_retry_strategy(self):
        """Test council retries on error with retry strategy."""
        from konseho.core.steps import StepResult
        retry_count = 0
        
        class RetryStep(Step):
            async def execute(self, task: str, context: Context):
                nonlocal retry_count
                retry_count += 1
                if retry_count == 1:
                    raise ValueError("First attempt fails")
                return StepResult(output="success", metadata={"status": "success"})
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="test",
            steps=[RetryStep()],
            error_strategy="retry"
        )
        
        result = await council.execute("Test task")
        assert retry_count == 2  # Initial + retry
        assert "results" in result
    
    def test_council_run_sync_wrapper(self):
        """Test synchronous run wrapper."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        step = ParallelStep([agent])
        factory = CouncilFactory()
        council = factory.create_council(name="test", steps=[step])
        
        # Should run without asyncio explicitly
        result = council.run("Test task")
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_council_event_emission(self):
        """Test council emits proper events."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        step = ParallelStep([agent])
        factory = CouncilFactory()
        council = factory.create_council(name="test", steps=[step])
        
        # Set up event collector
        collector = EventCollector()
        council._event_emitter.on("council_started", collector.collect)
        council._event_emitter.on("step_started", collector.collect)
        council._event_emitter.on("step_completed", collector.collect)
        council._event_emitter.on("council_completed", collector.collect)
        
        await council.execute("Test task")
        
        # Verify event sequence
        assert collector.has_event("council_started")
        assert collector.has_event("step_started")
        assert collector.has_event("step_completed")
        assert collector.has_event("council_completed")
        
        # Verify event order
        sequence = collector.get_event_sequence()
        assert sequence == [
            "council_started",
            "step_started",
            "step_completed",
            "council_completed"
        ]
    
    @pytest.mark.asyncio
    async def test_council_context_accumulation(self):
        """Test context accumulates results from steps."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Result 1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Result 2"))
        
        step1 = ParallelStep([agent1])
        step2 = ParallelStep([agent2])
        
        factory = CouncilFactory()
        council = factory.create_council(name="test", steps=[step1, step2])
        
        result = await council.execute("Test task")
        
        # Check context accumulated both step results
        context_results = council.context.get_results()
        assert "step_0" in context_results
        assert "step_1" in context_results