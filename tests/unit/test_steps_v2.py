"""Tests for refactored step implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from konseho.core.steps_v2 import (
    Step,
    StepResult,
    DebateStep,
    DebateConfig,
    ParallelStep,
)
from konseho.core.debate_components import (
    ProposalCollector,
    MajorityVoting,
    WeightedVoting,
    VotingSystem,
)
from konseho.core.parallel_strategies import (
    DomainParallelStrategy,
    TaskSplitStrategy,
    LoadBalancedStrategy,
)
from konseho.core.step_factory import StepFactory


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str, responses: list[str] | None = None):
        self.name = name
        self.responses = responses or ["Default response"]
        self.response_index = 0

    async def work_on(self, task: str) -> str:
        """Return next response in sequence."""
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1
        return response

    def get_capabilities(self) -> dict:
        """Return mock capabilities."""
        return {"expertise_level": 0.5}


class TestStepResult:
    """Test StepResult dataclass."""

    def test_step_result_creation(self):
        """Test creating a step result."""
        result = StepResult(
            output="Test output", metadata={"key": "value"}, error=None, success=True
        )

        assert result.output == "Test output"
        assert result.metadata == {"key": "value"}
        assert result.error is None
        assert result.success is True

    def test_step_result_defaults(self):
        """Test step result default values."""
        result = StepResult(output="Test")

        assert result.output == "Test"
        assert result.metadata == {}
        assert result.error is None
        assert result.success is True


class TestBaseStep:
    """Test base Step class."""

    def test_step_name(self):
        """Test step name is based on class name."""

        class TestStep(Step):
            async def execute(self, task, context):
                return StepResult(output="test")

        step = TestStep([])
        assert step.name == "TestStep"

    def test_step_validation(self):
        """Test step validation."""

        class TestStep(Step):
            async def execute(self, task, context):
                return StepResult(output="test")

            def get_required_agents(self):
                return 2

        # Not enough agents
        step = TestStep([MockAgent("agent1")])
        errors = step.validate()
        assert len(errors) == 1
        assert "requires at least 2 agents" in errors[0]

        # Enough agents
        step = TestStep([MockAgent("agent1"), MockAgent("agent2")])
        errors = step.validate()
        assert len(errors) == 0


class TestProposalCollector:
    """Test proposal collection component."""

    @pytest.mark.asyncio
    async def test_collect_proposals(self):
        """Test collecting proposals from agents."""
        agents = [
            MockAgent("agent1", ["Proposal 1"]),
            MockAgent("agent2", ["Proposal 2"]),
        ]

        collector = ProposalCollector()
        proposals = await collector.collect(agents, "Test task", None)

        assert len(proposals) == 2
        assert proposals["agent1"] == "Proposal 1"
        assert proposals["agent2"] == "Proposal 2"

    @pytest.mark.asyncio
    async def test_collect_with_moderator(self):
        """Test collecting proposals with moderator guidance."""
        agents = [
            MockAgent("agent1", ["Proposal 1"]),
            MockAgent("agent2", ["Proposal 2"]),
        ]
        moderator = MockAgent("moderator", ["Focus on efficiency"])

        collector = ProposalCollector()
        proposals = await collector.collect(agents, "Test task", moderator)

        # Should still get proposals from agents
        assert len(proposals) == 2
        assert "agent1" in proposals
        assert "agent2" in proposals


class TestVotingSystem:
    """Test voting system components."""

    @pytest.mark.asyncio
    async def test_majority_voting(self):
        """Test majority voting strategy."""
        agents = [
            MockAgent("agent1", ["I vote for: agent2"]),
            MockAgent("agent2", ["I vote for: agent2"]),
            MockAgent("agent3", ["I vote for: agent1"]),
        ]

        proposals = {
            "agent1": "Proposal 1",
            "agent2": "Proposal 2",
        }

        strategy = MajorityVoting()
        winner, metadata = await strategy.select_winner(agents, proposals)

        assert winner == "Proposal 2"
        assert metadata["votes"]["agent2"] == 2
        assert metadata["votes"]["agent1"] == 1
        assert metadata["total_votes"] == 3

    @pytest.mark.asyncio
    async def test_weighted_voting(self):
        """Test weighted voting strategy."""
        agents = [
            MockAgent("expert", ["I vote for: agent1"]),
            MockAgent("junior", ["I vote for: agent2"]),
        ]

        proposals = {
            "agent1": "Proposal 1",
            "agent2": "Proposal 2",
        }

        weights = {"expert": 2.0, "junior": 0.5}
        strategy = WeightedVoting(weights)
        winner, metadata = await strategy.select_winner(agents, proposals)

        assert winner == "Proposal 1"
        assert metadata["weighted_scores"]["agent1"] == 2.0
        assert metadata["weighted_scores"]["agent2"] == 0.5


class TestDebateStep:
    """Test refactored debate step."""

    @pytest.mark.asyncio
    async def test_debate_execution(self):
        """Test basic debate execution."""
        agents = [
            MockAgent(
                "agent1",
                ["Initial proposal 1", "Updated proposal 1", "I vote for: agent1"],
            ),
            MockAgent(
                "agent2",
                ["Initial proposal 2", "Updated proposal 2", "I vote for: agent2"],
            ),
        ]

        config = DebateConfig(rounds=1)
        step = DebateStep(agents, config)

        context = MagicMock()
        result = await step.execute("Test task", context)

        assert isinstance(result, StepResult)
        assert result.output in ["Initial proposal 1", "Initial proposal 2"]
        assert "all_proposals" in result.metadata
        assert "vote_details" in result.metadata

    def test_debate_validation(self):
        """Test debate step validation."""
        # Not enough agents
        step = DebateStep([MockAgent("agent1")])
        errors = step.validate()
        assert len(errors) == 1
        assert "at least 2 agents" in errors[0]

        # Invalid rounds
        config = DebateConfig(rounds=0)
        step = DebateStep([MockAgent("a1"), MockAgent("a2")], config)
        errors = step.validate()
        assert len(errors) == 1
        assert "at least 1 round" in errors[0]


class TestParallelStrategies:
    """Test parallel execution strategies."""

    @pytest.mark.asyncio
    async def test_domain_parallel_strategy(self):
        """Test domain-based parallel execution."""
        agents = [
            MockAgent("agent1", ["Technical analysis"]),
            MockAgent("agent2", ["Business analysis"]),
        ]

        strategy = DomainParallelStrategy(["technical", "business"])
        context = MagicMock()
        results = await strategy.execute_parallel(agents, "Test task", context)

        assert len(results) == 2
        assert any("technical" in key for key in results.keys())
        assert any("business" in key for key in results.keys())

        merged = strategy.merge_results(results)
        assert "Multi-perspective Analysis" in merged

    @pytest.mark.asyncio
    async def test_task_split_strategy(self):
        """Test task splitting strategy."""
        agents = [
            MockAgent("agent1", ["Result 1"]),
            MockAgent("agent2", ["Result 2"]),
        ]

        strategy = TaskSplitStrategy()
        context = MagicMock()
        results = await strategy.execute_parallel(agents, "Line 1\nLine 2", context)

        assert len(results) == 2
        assert "Subtask 1" in results
        assert "Subtask 2" in results

    @pytest.mark.asyncio
    async def test_load_balanced_strategy(self):
        """Test load balanced execution."""
        # Create agents with different capabilities
        agent1 = MockAgent("expert", ["Expert analysis"])
        agent1.get_capabilities = lambda: {"expertise_level": 0.9}

        agent2 = MockAgent("junior", ["Junior analysis"])
        agent2.get_capabilities = lambda: {"expertise_level": 0.3}

        agents = [agent1, agent2]

        strategy = LoadBalancedStrategy()
        context = MagicMock()
        results = await strategy.execute_parallel(agents, "Test task", context)

        assert len(results) == 2
        assert "expert" in results
        assert "junior" in results


class TestParallelStep:
    """Test refactored parallel step."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test basic parallel execution."""
        agents = [
            MockAgent("agent1", ["Result 1"]),
            MockAgent("agent2", ["Result 2"]),
        ]

        step = ParallelStep(agents)
        context = MagicMock()
        result = await step.execute("Test task", context)

        assert isinstance(result, StepResult)
        assert "Multi-perspective Analysis" in result.output
        assert "individual_results" in result.metadata
        assert len(result.metadata["individual_results"]) == 2


class TestStepFactory:
    """Test step factory."""

    def test_create_debate_step(self):
        """Test creating debate step via factory."""
        agents = [MockAgent("a1"), MockAgent("a2")]

        # Basic debate
        step = StepFactory.debate(agents)
        assert isinstance(step, DebateStep)
        assert step.rounds == 2

        # Weighted debate
        weights = {"a1": 2.0, "a2": 1.0}
        step = StepFactory.weighted_debate(agents, weights)
        assert isinstance(step, DebateStep)
        assert isinstance(step.voting_system.strategy, WeightedVoting)

    def test_create_parallel_step(self):
        """Test creating parallel step via factory."""
        agents = [MockAgent("a1"), MockAgent("a2")]

        # Domain parallel
        step = StepFactory.domain_parallel(agents, ["frontend", "backend"])
        assert isinstance(step, ParallelStep)
        assert isinstance(step.strategy, DomainParallelStrategy)

        # Task split
        step = StepFactory.task_split(agents)
        assert isinstance(step, ParallelStep)
        assert isinstance(step.strategy, TaskSplitStrategy)

        # Load balanced
        step = StepFactory.load_balanced(agents)
        assert isinstance(step, ParallelStep)
        assert isinstance(step.strategy, LoadBalancedStrategy)

