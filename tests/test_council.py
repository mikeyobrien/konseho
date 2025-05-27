"""Tests for council orchestration."""

from unittest.mock import Mock

import pytest

from konseho import AgentWrapper, Context, Council, ParallelStep


class MockAgent:
    """Mock Strands agent for testing."""
    def __call__(self, prompt):
        return Mock(message=f"Response to: {prompt[:20]}...")


def test_council_initialization():
    """Test council can be initialized."""
    council = Council(
        name="test_council",
        steps=[],
        error_strategy="halt"
    )
    assert council.name == "test_council"
    assert council.error_strategy == "halt"
    assert isinstance(council.context, Context)


@pytest.mark.asyncio
async def test_council_execution():
    """Test basic council execution flow."""
    # Create mock agents
    agent1 = MockAgent()
    agent2 = MockAgent()
    
    # Create council with parallel step
    step = ParallelStep([
        AgentWrapper(agent1, "agent1"),
        AgentWrapper(agent2, "agent2")
    ])
    
    council = Council(
        name="test_council",
        steps=[step]
    )
    
    # Execute
    result = await council.execute("Test task")
    
    assert "results" in result
    assert "data" in result