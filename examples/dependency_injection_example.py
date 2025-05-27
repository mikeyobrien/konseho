"""Example demonstrating dependency injection with Council."""

import asyncio
from typing import Any

from konseho.adapters import MockAgent, MockEventEmitter, MockOutputManager
from konseho.core.context import Context
from konseho.core.council import Council
from konseho.core.steps import DebateStep
from konseho.factories import CouncilDependencies, CouncilFactory


async def example_legacy_initialization():
    """Example showing the traditional way of creating a Council."""
    print("=== Legacy Council Initialization ===")

    # Create agents
    agents = [
        MockAgent("analyst", response="Analyze the data"),
        MockAgent("engineer", response="Build the system"),
        MockAgent("designer", response="Design the interface"),
    ]

    # Create council the old way (still works)
    council = Council(
        name="legacy_council",
        agents=agents,
        save_outputs=True,
        output_dir="legacy_outputs",
    )

    result = await council.execute("Create a new product")
    print(f"Legacy council completed: {result.get('results', {}).get('step_0', {})}")


async def example_dependency_injection():
    """Example showing dependency injection pattern."""
    print("\n=== Dependency Injection Example ===")

    # Create mock dependencies
    mock_context = Context({"initial_data": "test"})
    mock_event_emitter = MockEventEmitter()
    mock_output_manager = MockOutputManager()

    # Create dependencies container
    dependencies = CouncilDependencies(
        context=mock_context,
        event_emitter=mock_event_emitter,
        output_manager=mock_output_manager,
    )

    # Create agents
    agents = [
        MockAgent("researcher", response="Research findings"),
        MockAgent("writer", response="Written report"),
    ]

    # Create council with injected dependencies
    council = Council(name="injected_council", agents=agents, dependencies=dependencies)

    # Execute task
    result = await council.execute("Write a research report")

    # Verify mock event emitter captured events
    print(f"\nEmitted events: {len(mock_event_emitter.get_emitted_events())}")
    for event, data in mock_event_emitter.get_emitted_events():
        print(f"  - {event}: {data}")

    # Verify mock output manager saved outputs
    if mock_output_manager.saved_outputs:
        print(f"\nSaved outputs: {len(mock_output_manager.get_saved_outputs())}")
        for output in mock_output_manager.get_saved_outputs():
            print(f"  - Task: {output['task']}")


async def example_factory_pattern():
    """Example using the factory pattern."""
    print("\n=== Factory Pattern Example ===")

    # Create factory with custom dependencies
    factory = CouncilFactory(
        dependencies=CouncilDependencies(
            event_emitter=MockEventEmitter(), output_manager=MockOutputManager()
        )
    )

    # Create council using factory
    council = factory.create_council(
        name="factory_council",
        agents=[
            MockAgent("planner", response="Project plan"),
            MockAgent("executor", response="Execution complete"),
        ],
        save_outputs=True,
    )

    result = await council.execute("Plan and execute project")
    print("Factory council completed successfully")


async def example_testing_with_mocks():
    """Example showing how to test with mocks."""
    print("\n=== Testing with Mocks Example ===")

    # Create test factory
    factory = CouncilFactory()

    # Create test council with all mock dependencies
    test_council = factory.create_test_council(
        name="test_council",
        mock_context=Context(),
        mock_event_emitter=MockEventEmitter(),
        mock_output_manager=MockOutputManager(),
    )

    # Add test agents
    test_council.agents = [MockAgent("test_agent", response="Test response")]
    test_council.steps = [DebateStep(test_council.agents)]

    # Run test
    result = await test_council.execute("Test task")

    # Verify behavior
    event_emitter = test_council._event_emitter
    if hasattr(event_emitter, "get_emitted_events"):
        events = event_emitter.get_emitted_events()
        print(f"Test events captured: {len(events)}")

        # Verify expected events were emitted
        event_types = [event for event, _ in events]
        assert "council:start" in event_types
        assert "council:complete" in event_types
        print("✓ All expected events were emitted")


def example_custom_dependency_injection():
    """Example showing custom dependency implementations."""
    print("\n=== Custom Dependencies Example ===")

    # Create custom event emitter that logs to file
    class FileLoggingEventEmitter:
        def __init__(self, log_file: str):
            self.log_file = log_file
            self.events = []

        def on(self, event: str, handler: Any) -> None:
            pass

        def emit(self, event: str, data: Any = None) -> None:
            self.events.append(f"{event}: {data}")
            print(f"[FileLogger] {event}")

        async def emit_async(self, event: str, data: Any = None) -> None:
            self.emit(event, data)

    # Create custom context with persistence
    class PersistentContext(Context):
        def add(self, key: str, value: Any) -> None:
            super().add(key, value)
            print(f"[PersistentContext] Stored: {key} = {value}")

    # Use custom dependencies
    custom_deps = CouncilDependencies(
        context=PersistentContext(),
        event_emitter=FileLoggingEventEmitter("council.log"),
    )

    council = Council(
        name="custom_council", agents=[MockAgent("worker")], dependencies=custom_deps
    )

    print("✓ Council created with custom dependencies")


async def main():
    """Run all examples."""
    await example_legacy_initialization()
    await example_dependency_injection()
    await example_factory_pattern()
    await example_testing_with_mocks()
    example_custom_dependency_injection()

    print("\n=== Dependency Injection Benefits ===")
    print("✓ Easy testing with mock dependencies")
    print("✓ Swappable implementations at runtime")
    print("✓ Clear separation of concerns")
    print("✓ Backward compatibility maintained")
    print("✓ Follows SOLID principles")


if __name__ == "__main__":
    asyncio.run(main())
