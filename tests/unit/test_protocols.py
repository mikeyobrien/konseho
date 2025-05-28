"""Tests for protocol implementations and adapters."""

from typing import Any

import pytest

from konseho.adapters import (
    AgentAdapter,
    ContextAdapter,
    MockAgent,
    MockStep,
    StepAdapter,
)
from konseho.core.context import Context
from konseho.core.steps import Step, StepResult
from konseho.protocols import (
    IAgent,
    IContext,
    IStep,
    IStepResult,
)


class TestProtocols:
    """Test protocol definitions and runtime checking."""

    def test_mock_agent_implements_iagent(self):
        """Test that MockAgent correctly implements IAgent protocol."""
        agent = MockAgent("test", "mock-model", "test response")

        # Verify it's recognized as implementing IAgent
        assert isinstance(agent, IAgent)

        # Test all required properties/methods
        assert agent.name == "test"
        assert agent.model == "mock-model"
        assert agent.get_capabilities() == {"mock": True}

    @pytest.mark.asyncio
    async def test_mock_agent_work_on(self):
        """Test MockAgent's work_on method."""
        agent = MockAgent("test", "mock-model", "test response")
        result = await agent.work_on("test task")
        assert result == "test response"

    def test_mock_step_implements_istep(self):
        """Test that MockStep correctly implements IStep protocol."""
        step = MockStep("test_step", "test output")

        # Verify protocol implementation
        assert isinstance(step, IStep)

        # Test properties
        assert step.name == "test_step"
        assert step.validate() == []

    @pytest.mark.asyncio
    async def test_mock_step_execute(self):
        """Test MockStep's execute method."""
        step = MockStep("test_step", "test output")
        context = Context()

        result = await step.execute("test task", context)

        assert isinstance(result, IStepResult)
        assert result.output == "test output"
        assert result.success is True
        assert result.metadata == {"mock": True}

    def test_context_implements_icontext(self):
        """Test that Context implements IContext protocol."""
        context = Context()

        # Context should implement IContext
        assert isinstance(context, IContext)

        # Test all required methods
        context.add("key", "value")
        assert context.get("key") == "value"

        context.update({"key2": "value2", "key3": "value3"})
        assert context.get("key2") == "value2"

        data = context.to_dict()
        assert "key" in data
        assert "key2" in data

        size = context.get_size()
        assert isinstance(size, int)
        assert size > 0

        context.clear()
        assert context.get("key") is None


class TestAdapters:
    """Test adapter classes for migration support."""

    def test_agent_adapter(self):
        """Test AgentAdapter wraps existing agents correctly."""

        # Create a mock wrapped agent
        class MockWrappedAgent:
            def __init__(self):
                self.name = "wrapped"
                self.model = "test-model"

            async def work_on(self, task: str) -> str:
                return f"Wrapped result: {task}"

        wrapped = MockWrappedAgent()
        adapter = AgentAdapter(wrapped)

        # Should implement IAgent
        assert isinstance(adapter, IAgent)

        # Properties should pass through
        assert adapter.name == "wrapped"
        assert adapter.model == "test-model"

    def test_step_adapter_with_existing_step(self):
        """Test StepAdapter with existing Step class."""

        # Create a simple concrete step
        class TestStep(Step):
            @property
            def name(self):
                return "TestStep"

            async def execute(self, task: str, context: Context) -> dict[str, Any]:
                return {"output": "test result"}

        step = TestStep()
        adapter = StepAdapter(step)

        # Should implement IStep
        assert isinstance(adapter, IStep)
        assert adapter.name == "TestStep"
        assert adapter.validate() == []

    def test_context_adapter(self):
        """Test ContextAdapter wraps Context correctly."""
        context = Context({"initial": "data"})
        adapter = ContextAdapter(context)

        # Should implement IContext
        assert isinstance(adapter, IContext)

        # Test methods pass through
        adapter.add("new_key", "new_value")
        assert adapter.get("new_key") == "new_value"
        assert adapter.get("initial") == "data"

        # Test size calculation
        size = adapter.get_size()
        assert isinstance(size, int)
        assert size > 0


class TestProtocolValidation:
    """Test protocol validation for different implementations."""

    def test_custom_agent_implementation(self):
        """Test that custom classes can implement IAgent."""

        class MinimalAgent:
            @property
            def name(self) -> str:
                return "minimal"

            @property
            def model(self) -> str:
                return "minimal-model"

            async def work_on(self, task: str) -> str:
                return "done"

            def get_capabilities(self) -> dict[str, Any]:
                return {}

        agent = MinimalAgent()
        # Should be recognized as implementing IAgent
        assert isinstance(agent, IAgent)

    def test_incomplete_agent_implementation(self):
        """Test that incomplete implementations are not recognized."""

        class IncompleteAgent:
            @property
            def name(self) -> str:
                return "incomplete"

            # Missing model, work_on, and get_capabilities

        agent = IncompleteAgent()
        # Should NOT be recognized as implementing IAgent
        assert not isinstance(agent, IAgent)

    def test_step_result_protocol(self):
        """Test StepResult implements IStepResult."""
        result = StepResult("test output", {"meta": "data"})

        # StepResult should implement IStepResult
        assert isinstance(result, IStepResult)
        assert result.output == "test output"
        assert result.metadata == {"meta": "data"}
        assert result.success is True


class TestProtocolUsage:
    """Test practical usage of protocols."""

    def test_function_accepting_protocol(self):
        """Test functions that accept protocol types."""

        def process_agents(agents: list[IAgent]) -> dict[str, str]:
            """Function that works with any IAgent implementation."""
            return {agent.name: agent.model for agent in agents}

        # Should work with different implementations
        mock1 = MockAgent("mock1", "model1")
        mock2 = MockAgent("mock2", "model2")

        result = process_agents([mock1, mock2])
        assert result == {"mock1": "model1", "mock2": "model2"}

    @pytest.mark.asyncio
    async def test_protocol_based_workflow(self):
        """Test a workflow using only protocol interfaces."""

        async def run_workflow(
            agents: list[IAgent], steps: list[IStep], context: IContext
        ) -> str:
            """Workflow that uses only protocol interfaces."""
            # Add agent info to context
            for agent in agents:
                context.add(f"agent_{agent.name}", agent.get_capabilities())

            # Execute steps
            for step in steps:
                if step.validate():
                    return "Validation failed"

                result = await step.execute("test task", context)
                context.add(f"step_{step.name}_result", result.output)

            return "Workflow complete"

        # Create implementations
        agents = [MockAgent("a1"), MockAgent("a2")]
        steps = [MockStep("s1"), MockStep("s2")]
        context = Context()

        # Run workflow
        result = await run_workflow(agents, steps, context)
        assert result == "Workflow complete"

        # Check context was updated
        assert context.get("agent_a1") == {"mock": True}
        assert context.get("step_s1_result") == "Mock output"
