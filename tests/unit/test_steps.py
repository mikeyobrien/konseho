"""Unit tests for Step implementations."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from konseho import Context, DebateStep, ParallelStep, SplitStep, AgentWrapper
from konseho.core.steps import StepResult
from konseho.core.steps import Step
from tests.fixtures import MockStrandsAgent, MockAgent


class TestParallelStep:
    """Tests for ParallelStep execution."""
    
    @pytest.mark.asyncio
    async def test_parallel_execution_basic(self):
        """Test basic parallel execution of agents."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Response 1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Response 2"))
        
        step = ParallelStep([agent1, agent2])
        context = Context()
        
        result = await step.execute("Test task", context)
        
        assert isinstance(result, StepResult)
        assert "parallel_results" in result.metadata
        assert len(result.metadata["parallel_results"]) == 2
        assert "agent1" in result.metadata["parallel_results"]
        assert "agent2" in result.metadata["parallel_results"]
        assert "Response 1" in result.metadata["parallel_results"]["agent1"]
        assert "Response 2" in result.metadata["parallel_results"]["agent2"]
    
    @pytest.mark.asyncio
    async def test_parallel_execution_with_context(self):
        """Test parallel execution includes context in prompts."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))
        
        step = ParallelStep([agent1, agent2])
        context = Context({"existing": "data"})
        
        await step.execute("Test task", context)
        
        # Check agents received context
        assert any("Current Context:" in call for call in agent1.agent.call_history)
        assert any("existing" in call for call in agent1.agent.call_history)
    
    @pytest.mark.asyncio
    async def test_parallel_with_task_splitter(self):
        """Test parallel execution with custom task splitter."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))
        
        def splitter(task: str, num_agents: int):
            return [f"Part {i+1}: {task}" for i in range(num_agents)]
        
        step = ParallelStep([agent1, agent2], task_splitter=splitter)
        context = Context()
        
        await step.execute("Main task", context)
        
        # Check each agent got different subtask
        assert any("Part 1:" in call for call in agent1.agent.call_history)
        assert any("Part 2:" in call for call in agent2.agent.call_history)
    
    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self):
        """Test that agents truly execute in parallel."""
        # Create agents with delays
        agent1 = AgentWrapper(MockStrandsAgent("agent1", delay=0.1))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", delay=0.1))
        
        step = ParallelStep([agent1, agent2])
        context = Context()
        
        import time
        start = time.time()
        await step.execute("Test", context)
        duration = time.time() - start
        
        # If sequential, would take ~0.2s, parallel should be ~0.1s
        assert duration < 0.15  # Allow some overhead


class TestDebateStep:
    """Tests for DebateStep with voting and rounds."""
    
    @pytest.mark.asyncio
    async def test_debate_basic_execution(self):
        """Test basic debate execution."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Proposal 1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Proposal 2"))
        
        step = DebateStep([agent1, agent2], rounds=1)
        context = Context()
        
        result = await step.execute("Debate topic", context)
        
        assert isinstance(result, StepResult)
        assert "proposals" in result.metadata
        assert "winner" in result.metadata
        assert "strategy" in result.metadata
        assert result.metadata["strategy"] == "majority"
    
    @pytest.mark.asyncio
    async def test_debate_multiple_rounds(self):
        """Test debate with multiple rounds."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Proposal"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Proposal"))
        
        step = DebateStep([agent1, agent2], rounds=2)
        context = Context()
        
        result = await step.execute("Topic", context)
        
        # Should have initial proposals + round proposals
        assert isinstance(result, StepResult)
        proposals = result.metadata["proposals"]
        assert "agent1" in proposals
        assert "agent2" in proposals
        assert "agent1_round_0" in proposals
        assert "agent2_round_0" in proposals
        assert "agent1_round_1" in proposals
        assert "agent2_round_1" in proposals
    
    @pytest.mark.asyncio
    async def test_debate_with_moderator(self):
        """Test debate with moderator selecting winner."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1", "Proposal 1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2", "Proposal 2"))
        moderator = AgentWrapper(MockStrandsAgent("moderator", "agent1 wins"))
        
        step = DebateStep(
            [agent1, agent2],
            moderator=moderator,
            voting_strategy="moderator"
        )
        context = Context()
        
        result = await step.execute("Topic", context)
        
        assert isinstance(result, StepResult)
        assert result.metadata["strategy"] == "moderator"
        assert "agent1 wins" in result.metadata["winner"]
    
    @pytest.mark.asyncio
    async def test_debate_context_in_prompts(self):
        """Test debate includes context in agent prompts."""
        agent1 = AgentWrapper(MockStrandsAgent("agent1"))
        agent2 = AgentWrapper(MockStrandsAgent("agent2"))
        
        step = DebateStep([agent1, agent2], rounds=1)
        context = Context({"background": "important context"})
        
        await step.execute("Topic", context)
        
        # Initial proposals should include context
        assert any("Current Context:" in call for call in agent1.agent.call_history)
        assert any("background" in call for call in agent1.agent.call_history)


class TestSplitStep:
    """Tests for SplitStep dynamic agent creation."""
    
    @pytest.mark.asyncio
    async def test_split_fixed_strategy(self):
        """Test split with fixed number of agents."""
        template = MockStrandsAgent("template")
        
        step = SplitStep(
            agent_template=template,
            min_agents=3,
            max_agents=10,
            split_strategy="fixed"
        )
        context = Context()
        
        result = await step.execute("Task", context)
        
        assert "split_results" in result
        assert "num_agents" in result
        assert result["num_agents"] == 3  # Should use min_agents
        assert len(result["split_results"]) == 3
    
    @pytest.mark.asyncio 
    async def test_split_auto_strategy(self):
        """Test split with auto strategy based on task complexity."""
        template = MockStrandsAgent("template")
        
        step = SplitStep(
            agent_template=template,
            min_agents=2,
            max_agents=5,
            split_strategy="auto"
        )
        context = Context()
        
        # Short task
        result = await step.execute("Short task", context)
        assert isinstance(result, StepResult)
        assert result.metadata["num_agents"] == 2  # Minimum
        
        # Longer task
        long_task = " ".join(["word"] * 100)  # 100 words
        result = await step.execute(long_task, context)
        assert isinstance(result, StepResult)
        assert result.metadata["num_agents"] == 3  # Based on heuristic
    
    @pytest.mark.asyncio
    async def test_split_max_agents_limit(self):
        """Test split respects max agents limit."""
        template = MockStrandsAgent("template")
        
        step = SplitStep(
            agent_template=template,
            min_agents=2,
            max_agents=3,
            split_strategy="auto"
        )
        context = Context()
        
        # Very long task
        very_long_task = " ".join(["word"] * 500)
        result = await step.execute(very_long_task, context)
        
        assert isinstance(result, StepResult)
        assert result.metadata["num_agents"] == 3  # Should cap at max_agents
    
    @pytest.mark.asyncio
    async def test_split_task_distribution(self):
        """Test split distributes task parts to agents."""
        template = MockStrandsAgent("template")
        
        step = SplitStep(
            agent_template=template,
            min_agents=3,
            split_strategy="fixed"
        )
        context = Context()
        
        result = await step.execute("Main task", context)
        
        # Each result should indicate its part
        assert isinstance(result, StepResult)
        assert all("Part" in str(r) for r in result.metadata["split_results"])
        assert "Part 1/3" in str(result.metadata["split_results"][0])
        assert "Part 2/3" in str(result.metadata["split_results"][1])
        assert "Part 3/3" in str(result.metadata["split_results"][2])


class TestStepInterface:
    """Test Step abstract interface."""
    
    def test_step_must_implement_execute(self):
        """Test Step requires execute implementation."""
        with pytest.raises(TypeError):
            # Can't instantiate abstract class
            Step()
    
    @pytest.mark.asyncio
    async def test_custom_step_implementation(self):
        """Test custom step implementation."""
        class CustomStep(Step):
            async def execute(self, task: str, context: Context):
                context.add("custom", "data")
                return StepResult(
                    output="Custom step complete",
                    metadata={"status": "custom_complete"}
                )
        
        step = CustomStep()
        context = Context()
        result = await step.execute("Task", context)
        
        assert isinstance(result, StepResult)
        assert result.metadata["status"] == "custom_complete"
        assert context.get("custom") == "data"