"""Unit tests for agent cloning functionality."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from konseho.agents.base import AgentWrapper
from konseho.core.steps import SplitStep
from tests.fixtures import MockStrandsAgent


class TestAgentCloning:
    """Tests for agent cloning in SplitStep and AgentWrapper."""

    def test_agent_wrapper_clone_basic(self):
        """Test basic cloning of an AgentWrapper."""
        original_agent = MockStrandsAgent("original", "Original response")
        wrapper = AgentWrapper(original_agent, name="wrapper1")

        # Clone the wrapper
        cloned = wrapper.clone("wrapper2")

        assert cloned.name == "wrapper2"
        assert cloned.agent is not original_agent  # Should be a new instance
        assert type(cloned.agent) == type(original_agent)
        assert cloned.agent.name == original_agent.name
        assert cloned.agent.response == original_agent.response

    def test_agent_wrapper_clone_with_tools(self):
        """Test cloning preserves agent tools and configuration."""
        # Mock a Strands agent with tools
        mock_agent = Mock()
        mock_agent.name = "agent_with_tools"
        mock_agent.tools = ["tool1", "tool2"]
        mock_agent.model = "gpt-4"
        mock_agent.temperature = 0.7

        wrapper = AgentWrapper(mock_agent, name="original")
        cloned = wrapper.clone("cloned")

        # Check that original tools are preserved (additional tools may be injected)
        assert cloned.agent.tools[:2] == ["tool1", "tool2"]
        assert cloned.agent.model == "gpt-4"
        assert cloned.agent.temperature == 0.7

    def test_agent_wrapper_clone_with_system_prompt(self):
        """Test cloning preserves system prompts."""
        mock_agent = Mock()
        mock_agent.system_prompt = "You are a helpful assistant"
        mock_agent.name = "prompted_agent"

        wrapper = AgentWrapper(mock_agent, name="original")
        wrapper.system_prompt_override = "You are an expert coder"

        cloned = wrapper.clone("cloned")

        assert cloned.agent.system_prompt == "You are a helpful assistant"
        assert cloned.system_prompt_override == "You are an expert coder"

    def test_split_step_create_agent_clones(self):
        """Test SplitStep creates proper agent clones."""
        template_agent = MockStrandsAgent("template", "Template response")
        step = SplitStep(agent_template=template_agent)

        clones = step._create_agent_clones(3)

        assert len(clones) == 3
        assert all(isinstance(c, AgentWrapper) for c in clones)
        assert all(c.name == f"split_agent_{i}" for i, c in enumerate(clones))

        # Each clone should be independent
        assert all(c.agent is not template_agent for c in clones)
        assert all(type(c.agent) == type(template_agent) for c in clones)

    def test_clone_preserves_agent_state(self):
        """Test that cloning preserves agent state but creates new instance."""
        original = MockStrandsAgent("stateful", "Response")
        original.call_count = 5
        original.call_history = ["prompt1", "prompt2"]

        wrapper = AgentWrapper(original)
        cloned = wrapper.clone("cloned")

        # State should be reset for clone
        assert cloned.agent.call_count == 0
        assert cloned.agent.call_history == []

        # But configuration should be preserved
        assert cloned.agent.name == "stateful"
        assert cloned.agent.response == "Response"

    def test_clone_with_custom_attributes(self):
        """Test cloning with custom attributes."""
        wrapper = AgentWrapper(
            MockStrandsAgent("original"),
            name="wrapper1",
            expertise_level=0.9,
            domain="backend",
        )

        cloned = wrapper.clone("wrapper2")

        assert cloned.expertise_level == 0.9
        assert cloned.domain == "backend"

    def test_clone_deep_copy_safety(self):
        """Test that cloning doesn't share mutable objects."""
        mock_agent = Mock()
        mock_agent.config = {"key": ["value1", "value2"]}
        mock_agent.name = "configurable"

        wrapper = AgentWrapper(mock_agent)
        cloned = wrapper.clone("cloned")

        # Modify original config
        mock_agent.config["key"].append("value3")

        # Clone should not be affected
        assert len(cloned.agent.config["key"]) == 2

    @patch("konseho.agents.base.create_agent")
    def test_clone_with_strands_agent(self, mock_create_agent):
        """Test cloning with actual Strands agent creation."""
        # Mock the Strands agent creation
        mock_strands_agent = MagicMock()
        mock_strands_agent.name = "strands_agent"
        mock_strands_agent.model = "gpt-4"
        mock_strands_agent.tools = []
        mock_create_agent.return_value = mock_strands_agent

        wrapper = AgentWrapper(mock_strands_agent, name="original")
        cloned = wrapper.clone("cloned")

        # Should create a new agent with same config
        mock_create_agent.assert_called_once()
        assert cloned.name == "cloned"
        assert cloned.agent.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_cloned_agents_work_independently(self):
        """Test that cloned agents can work independently."""
        template = MockStrandsAgent("template", "Base response")
        step = SplitStep(agent_template=template, min_agents=3)

        clones = step._create_agent_clones(3)

        # Each clone should work independently
        responses = []
        for i, clone in enumerate(clones):
            # Override response for testing
            clone.agent.response = f"Response {i}"
            response = await clone.work_on(f"Task {i}")
            responses.append(response)

        assert responses == [
            "Response 0 (call 1)",
            "Response 1 (call 1)",
            "Response 2 (call 1)",
        ]

        # Verify each maintained its own state
        assert all(clone.agent.call_count == 1 for clone in clones)
        assert clones[0].agent.call_history == ["Task 0"]
        assert clones[1].agent.call_history == ["Task 1"]
        assert clones[2].agent.call_history == ["Task 2"]
