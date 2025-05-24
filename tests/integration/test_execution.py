"""Integration tests for council execution flow."""

import pytest
import asyncio
from unittest.mock import Mock, patch

from konseho import (
    Council, Context, AgentWrapper, HumanAgent,
    DebateStep, ParallelStep, SplitStep,
    AsyncExecutor
)
from tests.fixtures import MockStrandsAgent, EventCollector


class TestFullCouncilExecution:
    """Test complete council execution flows."""
    
    @pytest.mark.asyncio
    async def test_simple_council_execution(self):
        """Test simple single-step council execution."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Solution A"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Solution B"))
        
        council = Council(
            name="simple_council",
            steps=[ParallelStep([agent1, agent2])]
        )
        
        result = await council.execute("Solve problem X")
        
        assert "results" in result
        assert "step_0" in result["results"]
        assert "parallel_results" in result["results"]["step_0"]
        assert len(result["results"]["step_0"]["parallel_results"]) == 2
    
    @pytest.mark.asyncio
    async def test_multi_step_council_execution(self):
        """Test council with multiple sequential steps."""
        # Step 1: Parallel analysis
        analyst1 = AgentWrapper(MockStrandsAgent("analyst1", "Analysis A"))
        analyst2 = AgentWrapper(MockStrandsAgent("analyst2", "Analysis B"))
        
        # Step 2: Debate solutions
        debater1 = AgentWrapper(MockStrandsAgent("debater1", "Solution 1"))
        debater2 = AgentWrapper(MockStrandsAgent("debater2", "Solution 2"))
        
        council = Council(
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
        
        # Verify step types
        assert "parallel_results" in result["results"]["step_0"]
        assert "proposals" in result["results"]["step_1"]
        assert "winner" in result["results"]["step_1"]
    
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
        
        council = Council(
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
        
        council = Council(
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
        
        council = Council(
            name="error_continue",
            steps=[
                ParallelStep([good_agent]),
                ParallelStep([bad_agent]),  # This will fail
                ParallelStep([good_agent])   # This should still execute
            ],
            error_strategy="continue"
        )
        
        result = await council.execute("Task")
        
        # First and third steps should have executed
        assert "step_0" in result["results"]
        assert "step_1" not in result["results"]  # Failed step
        assert "step_2" in result["results"]


class TestAsyncExecutor:
    """Test AsyncExecutor for parallel council execution."""
    
    @pytest.mark.asyncio
    async def test_executor_single_council(self):
        """Test executor with single council."""
        agent = AgentWrapper(MockStrandsAgent("agent"))
        council = Council("test", [ParallelStep([agent])])
        
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
            council = Council(f"council_{i}", [ParallelStep([agent])])
            councils.append(council)
        
        tasks = ["Task 1", "Task 2", "Task 3"]
        
        executor = AsyncExecutor(max_concurrent=2)
        results = await executor.execute_many(councils, tasks)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert "results" in result
            assert f"Result {i}" in str(result)
    
    @pytest.mark.asyncio
    async def test_executor_concurrency_limit(self):
        """Test executor respects concurrency limit."""
        # Create councils with delays to test concurrency
        councils = []
        for i in range(4):
            agent = AgentWrapper(MockStrandsAgent(f"agent_{i}", delay=0.1))
            council = Council(f"council_{i}", [ParallelStep([agent])])
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
        assert duration < 0.3    # But not sequential (0.4s)
    
    @pytest.mark.asyncio
    async def test_executor_error_handling(self):
        """Test executor handles council errors properly."""
        # Mix of good and bad councils
        good_agent = AgentWrapper(MockStrandsAgent("good"))
        
        class FailingAgent:
            def __call__(self, prompt):
                raise ValueError("Council failed")
        
        councils = [
            Council("good1", [ParallelStep([good_agent])]),
            Council("bad", [ParallelStep([AgentWrapper(FailingAgent())])]),
            Council("good2", [ParallelStep([good_agent])])
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
        councils = [Council("c1", [])]
        tasks = ["Task 1", "Task 2"]
        
        executor = AsyncExecutor()
        
        with pytest.raises(ValueError, match="Number of councils must match"):
            await executor.execute_many(councils, tasks)