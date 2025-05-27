"""Example demonstrating the use of protocols for loose coupling and testing."""

import asyncio
from typing import Dict, Any, List

from konseho.protocols import IAgent, IStep, IContext, IStepResult
from konseho.adapters import MockAgent, MockStep, AgentAdapter, StepAdapter
from konseho.core.council import Council
from konseho.core.context import Context
from konseho.core.steps import DebateStep
from konseho.agents.base import create_agent


async def example_with_mock_agents():
    """Example using mock agents for testing."""
    print("=== Example with Mock Agents ===")

    # Create mock agents that implement IAgent protocol
    mock_agents = [
        MockAgent("analyst", response="We should analyze the data first"),
        MockAgent("designer", response="We need a user-friendly interface"),
        MockAgent("engineer", response="Let's build a scalable architecture"),
    ]

    # Verify they implement the protocol
    for agent in mock_agents:
        assert isinstance(agent, IAgent), f"{agent.name} doesn't implement IAgent"
        print(f"✓ {agent.name} implements IAgent protocol")

    # Create a mock step
    mock_step = MockStep("planning", output="Combined plan: Analyze, Design, Build")
    assert isinstance(mock_step, IStep), "MockStep doesn't implement IStep"
    print("✓ MockStep implements IStep protocol")

    # Use mocks in a council
    council = Council(name="mock_council", steps=[mock_step])

    result = await council.execute("Build a recommendation system")
    print(f"\nMock Council Result: {result}")


async def example_with_protocol_validation():
    """Example showing protocol validation at runtime."""
    print("\n=== Example with Protocol Validation ===")

    # Create a custom agent that implements the protocol
    class CustomAgent:
        def __init__(self, name: str, model: str):
            self._name = name
            self._model = model

        @property
        def name(self) -> str:
            return self._name

        @property
        def model(self) -> str:
            return self._model

        async def work_on(self, task: str) -> str:
            return f"{self.name} working on: {task}"

        def get_capabilities(self) -> Dict[str, Any]:
            return {"custom": True}

    # Create instance and validate
    custom_agent = CustomAgent("custom_worker", "custom-model")

    # Runtime check that it implements IAgent
    if isinstance(custom_agent, IAgent):
        print("✓ CustomAgent implements IAgent protocol")
    else:
        print("✗ CustomAgent does NOT implement IAgent protocol")

    # Test the agent
    result = await custom_agent.work_on("Test task")
    print(f"Custom agent result: {result}")


async def example_with_adapters():
    """Example using adapters to migrate existing code."""
    print("\n=== Example with Adapters ===")

    # Create a real agent
    real_agent = await create_agent(name="researcher", model="claude-3-haiku-20240307")

    # Wrap it with an adapter
    adapted_agent = AgentAdapter(real_agent)

    # Verify it implements the protocol
    assert isinstance(adapted_agent, IAgent), "AgentAdapter doesn't implement IAgent"
    print("✓ AgentAdapter implements IAgent protocol")

    # Get capabilities
    capabilities = adapted_agent.get_capabilities()
    print(f"Agent capabilities: {capabilities}")

    # Create a debate step with adapted agents
    agents = [adapted_agent]  # Would have more in real scenario
    debate_step = DebateStep(agents=[real_agent])  # Original still works

    # Wrap with adapter
    adapted_step = StepAdapter(debate_step)
    assert isinstance(adapted_step, IStep), "StepAdapter doesn't implement IStep"
    print("✓ StepAdapter implements IStep protocol")

    # Validate the step
    errors = adapted_step.validate()
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("✓ Step validation passed")


def example_type_checking():
    """Example showing type checking with protocols."""
    print("\n=== Example with Type Checking ===")

    def process_agent(agent: IAgent) -> str:
        """Function that accepts any IAgent implementation."""
        return f"Processing agent: {agent.name} using {agent.model}"

    def execute_step(step: IStep, context: IContext) -> None:
        """Function that works with protocol interfaces."""
        errors = step.validate()
        if errors:
            print(f"Step {step.name} has errors: {errors}")
        else:
            print(f"Step {step.name} is valid")

    # Create different implementations
    mock = MockAgent("test", "mock-model")
    print(process_agent(mock))

    # Create context that implements IContext
    ctx = Context()
    mock_step = MockStep("test_step")
    execute_step(mock_step, ctx)


async def main():
    """Run all examples."""
    await example_with_mock_agents()
    await example_with_protocol_validation()

    try:
        await example_with_adapters()
    except Exception as e:
        print(f"\nSkipping adapter example (requires API key): {e}")

    example_type_checking()

    print("\n=== Protocol Benefits Demonstrated ===")
    print("✓ Loose coupling - components depend on interfaces, not implementations")
    print("✓ Easy testing - mock implementations for unit tests")
    print("✓ Type safety - runtime protocol checking")
    print("✓ Extensibility - new implementations without changing existing code")
    print("✓ Gradual migration - adapters allow incremental adoption")


if __name__ == "__main__":
    asyncio.run(main())
