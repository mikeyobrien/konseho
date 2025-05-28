"""Integration tests for council execution flow."""

from unittest.mock import Mock

import pytest

from konseho import (
    AgentWrapper,
    AsyncExecutor,
    Council,
    DebateStep,
    ParallelStep,
)
from konseho.factories import CouncilFactory
from tests.fixtures import MockStrandsAgent


class TestFullCouncilExecution:
    """Test complete council execution flows."""
    
    @pytest.mark.asyncio
    async def test_simple_council_execution(self):
        """Test simple single-step council execution."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Solution A"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Solution B"))
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="simple_council",
            steps=[ParallelStep([agent1, agent2])]
        )
        
        result = await council.execute("Solve problem X")
        
        assert "results" in result
        assert "step_0" in result["results"]
        # Step results are now StepResult objects with output and metadata
        step_result = result["results"]["step_0"]
        assert hasattr(step_result, "output")
        assert hasattr(step_result, "metadata")
        # ParallelStep puts results in metadata
        assert "parallel_results" in step_result.metadata
        assert len(step_result.metadata["parallel_results"]) == 2
    
    @pytest.mark.asyncio
    async def test_multi_step_council_execution(self):
        """Test council with multiple sequential steps."""
        # Step 1: Parallel analysis
        analyst1 = AgentWrapper(MockStrandsAgent("analyst1", "Analysis A"))
        analyst2 = AgentWrapper(MockStrandsAgent("analyst2", "Analysis B"))
        
        # Step 2: Debate solutions
        debater1 = AgentWrapper(MockStrandsAgent("debater1", "Solution 1"))
        debater2 = AgentWrapper(MockStrandsAgent("debater2", "Solution 2"))
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="multi_step",
            steps=[
                ParallelStep([analyst1, analyst2]),
                DebateStep([debater1, debater2], rounds=1)
            ]
        )
        
        result = await council.execute("Complex problem")
        
        # Verify both steps executed
        assert "step_0" in result["results"]
        assert "step_1" in result["results"]
        
        # Verify step types - results are now StepResult objects
        step0_result = result["results"]["step_0"]
        assert hasattr(step0_result, "metadata")
        assert "parallel_results" in step0_result.metadata
        
        step1_result = result["results"]["step_1"]
        assert hasattr(step1_result, "output")  # winner is in output
        assert hasattr(step1_result, "metadata")
        assert "proposals" in step1_result.metadata
        assert "votes" in step1_result.metadata
    
    @pytest.mark.asyncio
    async def test_council_context_flow(self):
        """Test context flows between steps."""
        # Create agents that check context
        class ContextAwareAgent:
            def __init__(self, name):
                self.name = name
                self.saw_previous_results = False
            
            def __call__(self, prompt):
                if "step_0" in prompt:
                    self.saw_previous_results = True
                return Mock(message=f"{self.name} response")
        
        agent1 = ContextAwareAgent("agent1")
        agent2 = ContextAwareAgent("agent2")
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="context_flow",
            steps=[
                ParallelStep([AgentWrapper(MockStrandsAgent("setup"))]),
                ParallelStep([AgentWrapper(agent1), AgentWrapper(agent2)])
            ]
        )
        
        await council.execute("Task")
        
        # Second step agents should have seen first step results
        assert agent1.saw_previous_results
        assert agent2.saw_previous_results
    
    @pytest.mark.asyncio
    async def test_council_error_handling_halt(self):
        """Test council halts on error with halt strategy."""
        good_agent = AgentWrapper(MockStrandsAgent("good"))
        
        # Agent that fails
        class FailingAgent:
            def __call__(self, prompt):
                raise ValueError("Agent failure")
        
        bad_agent = AgentWrapper(FailingAgent())
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="error_test",
            steps=[
                ParallelStep([good_agent]),
                ParallelStep([bad_agent]),  # This will fail
                ParallelStep([good_agent])   # This won't execute
            ],
            error_strategy="halt"
        )
        
        with pytest.raises(ValueError, match="Agent failure"):
            await council.execute("Task")
        
        # Only first step should have executed
        assert "step_0" in council.context.get_results()
        assert "step_1" not in council.context.get_results()
        assert "step_2" not in council.context.get_results()
    
    @pytest.mark.asyncio
    async def test_council_error_handling_continue(self):
        """Test council continues after error with continue strategy."""
        good_agent = AgentWrapper(MockStrandsAgent("good", "Success"))
        
        # Agent that fails
        class FailingAgent:
            def __call__(self, prompt):
                raise ValueError("Agent failure")
        
        bad_agent = AgentWrapper(FailingAgent())
        
        factory = CouncilFactory()
        council = factory.create_council(
            name="error_continue",
            steps=[
                ParallelStep([good_agent]),
                ParallelStep([bad_agent]),  # This will fail
                ParallelStep([good_agent])   # This should still execute
            ],
            error_strategy="continue"
        )
        
        result = await council.execute("Task")
        
        # All steps should be in results (continue strategy includes failed steps)
        assert "step_0" in result["results"]
        assert "step_1" in result["results"]  # Failed step is included with error info
        assert "step_2" in result["results"]
        
        # Check that step_1 has error metadata
        step1_result = result["results"]["step_1"]
        assert hasattr(step1_result, "metadata")
        assert "error" in step1_result.metadata
        assert "Agent failure" in step1_result.metadata["error"]
        assert step1_result.metadata.get("skipped") is True


class TestAsyncExecutor:
    """Test AsyncExecutor for parallel council execution."""
    
    @pytest.mark.asyncio
    async def test_executor_single_council(self):
        """Test executor with single council."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        factory = CouncilFactory()
        council = factory.create_council("test", [ParallelStep([agent])])
        
        executor = AsyncExecutor()
        result = await executor.execute_council(council, "Task")
        
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_executor_parallel_councils(self):
        """Test executor running multiple councils in parallel."""
        # Create multiple councils
        councils = []
        for i in range(3):
            agent = AgentWrapper(MockStrandsAgent(f"agent_{i}", f"Result {i}"))
            factory = CouncilFactory()
            council = factory.create_council(f"council_{i}", [ParallelStep([agent])])
            councils.append(council)
        
        tasks = ["Task 1", "Task 2", "Task 3"]
        
        executor = AsyncExecutor(max_concurrent=2)
        results = await executor.execute_many(councils, tasks)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert "results" in result
            # Check the actual agent output is in the step result
            step_result = result["results"]["step_0"]
            assert hasattr(step_result, "metadata")
            parallel_results = step_result.metadata.get("parallel_results", {})
            # Find the agent's output in parallel results
            agent_output = next(iter(parallel_results.values())) if parallel_results else ""
            assert f"Result {i}" in agent_output
    
    @pytest.mark.asyncio
    async def test_executor_concurrency_limit(self):
        """Test executor respects concurrency limit."""
        # Create councils with delays to test concurrency
        councils = []
        for i in range(4):
            agent = AgentWrapper(MockStrandsAgent(f"agent_{i}", delay=0.1))
            factory = CouncilFactory()
            council = factory.create_council(f"council_{i}", [ParallelStep([agent])])
            councils.append(council)
        
        tasks = ["Task"] * 4
        
        # With concurrency limit of 2
        executor = AsyncExecutor(max_concurrent=2)
        
        import time
        start = time.time()
        await executor.execute_many(councils, tasks)
        duration = time.time() - start
        
        # Should take ~0.2s (2 batches of 2) not 0.1s (all parallel)
        assert duration >= 0.15  # Allow some overhead
        assert duration < 0.5    # But not fully sequential (would be ~0.4s+overhead)
    
    @pytest.mark.asyncio
    async def test_executor_error_handling(self):
        """Test executor handles council errors properly."""
        # Mix of good and bad councils
        good_agent = AgentWrapper(MockStrandsAgent("good"))
        
        class FailingAgent:
            def __call__(self, prompt):
                raise ValueError("Council failed")
        
        factory = CouncilFactory()
        councils = [
            factory.create_council("good1", [ParallelStep([good_agent])]),
            factory.create_council("bad", [ParallelStep([AgentWrapper(FailingAgent())])]),
            factory.create_council("good2", [ParallelStep([good_agent])])
        ]
        
        tasks = ["Task 1", "Task 2", "Task 3"]
        
        executor = AsyncExecutor()
        results = await executor.execute_many(councils, tasks)
        
        assert len(results) == 3
        
        # Check results
        assert "results" in results[0]  # Good council
        assert "error" in results[1]     # Failed council
        assert results[1]["error"] == "Council failed"
        assert results[1]["council"] == "bad"
        assert "results" in results[2]   # Good council
    
    @pytest.mark.asyncio
    async def test_executor_mismatched_councils_tasks(self):
        """Test executor validates council/task count match."""
        factory = CouncilFactory()
        councils = [factory.create_council("c1", [])]
        tasks = ["Task 1", "Task 2"]
        
        executor = AsyncExecutor()
        
        with pytest.raises(ValueError, match="Number of councils must match"):
            await executor.execute_many(councils, tasks)