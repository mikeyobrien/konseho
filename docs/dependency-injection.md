# Dependency Injection in Konseho

This document explains the dependency injection pattern implemented for the Council class, improving testability and following SOLID principles.

## Overview

The Council class now supports dependency injection, allowing you to:
- Replace dependencies with mocks for testing
- Swap implementations at runtime
- Follow the Dependency Inversion Principle
- Maintain backward compatibility with existing code

## Architecture

### Core Components

1. **CouncilDependencies** - Container for all Council dependencies
2. **CouncilFactory** - Factory for creating Council instances
3. **Protocol Interfaces** - IContext, IEventEmitter, IOutputManager
4. **Mock Implementations** - For testing purposes

### Dependency Flow

```
CouncilFactory
    └── CouncilDependencies
            ├── IContext (Context)
            ├── IEventEmitter (EventEmitter)
            └── IOutputManager (OutputManager)
                    ↓
                Council
```

## Usage

### Standard Pattern with Factory

```python
from konseho.factories import CouncilFactory
from konseho.agents.base import create_agent

# Create agents
agent1 = await create_agent("agent1")
agent2 = await create_agent("agent2")

# Use factory to create council
factory = CouncilFactory()
council = factory.create_council(
    name="my_council",
    agents=[agent1, agent2],
    save_outputs=True,
    output_dir="outputs"
)

result = await council.execute("task")
```

### Advanced Dependency Injection

```python
from konseho.factories import CouncilFactory, CouncilDependencies
from konseho.core.context import Context

# Create custom dependencies
custom_context = Context({"initial_state": "ready"})
dependencies = CouncilDependencies(context=custom_context)

# Create council with injected dependencies
council = Council(
    name="my_council",
    agents=[agent1, agent2],
    dependencies=dependencies
)
```

### Using the Factory

```python
from konseho.factories import CouncilFactory

# Create factory with custom dependencies
factory = CouncilFactory(
    dependencies=CouncilDependencies.with_output_manager("outputs")
)

# Create councils using the factory
council1 = factory.create_council(
    name="council1",
    agents=[agent1, agent2]
)

council2 = factory.create_council(
    name="council2",
    agents=[agent3, agent4]
)
```

## Testing

### Using Mock Dependencies

```python
from konseho.adapters import MockEventEmitter, MockOutputManager
from konseho.factories import CouncilFactory, CouncilDependencies

# Create mock dependencies
mock_emitter = MockEventEmitter()
mock_output = MockOutputManager()

deps = CouncilDependencies(
    event_emitter=mock_emitter,
    output_manager=mock_output
)

# Create council with mocks
council = Council(
    name="test_council",
    agents=[MockAgent("test")],
    dependencies=deps
)

# Run test
await council.execute("test task")

# Verify behavior
events = mock_emitter.get_emitted_events()
assert ("council:start", {"council": "test_council", "task": "test task"}) in events

outputs = mock_output.get_saved_outputs()
assert len(outputs) == 1
```

### Test Factory

```python
factory = CouncilFactory()

# Create test council with all mocks
test_council = factory.create_test_council(
    name="test",
    mock_context=MockContext(),
    mock_event_emitter=MockEventEmitter(),
    mock_output_manager=MockOutputManager()
)
```

## Mock Implementations

### MockEventEmitter

Records all emitted events for verification:

```python
mock_emitter = MockEventEmitter()

# Use in council...

# Verify events
events = mock_emitter.get_emitted_events()
for event, data in events:
    print(f"{event}: {data}")

# Clear for next test
mock_emitter.clear()
```

### MockOutputManager

Captures saved outputs without file I/O:

```python
mock_output = MockOutputManager()

# Use in council...

# Verify outputs
outputs = mock_output.get_saved_outputs()
assert outputs[0]["task"] == "expected task"
assert outputs[0]["council_name"] == "test_council"
```

## Custom Implementations

You can create custom implementations of any dependency:

```python
class AuditingEventEmitter:
    """Event emitter that logs all events to audit trail."""
    
    def __init__(self, audit_log: AuditLog):
        self.audit_log = audit_log
        self.emitter = EventEmitter()
    
    def on(self, event: str, handler: Any) -> None:
        self.emitter.on(event, handler)
    
    def emit(self, event: str, data: Any = None) -> None:
        self.audit_log.record(event, data)
        self.emitter.emit(event, data)
    
    async def emit_async(self, event: str, data: Any = None) -> None:
        await self.audit_log.record_async(event, data)
        await self.emitter.emit_async(event, data)

# Use custom implementation
deps = CouncilDependencies(
    event_emitter=AuditingEventEmitter(audit_log)
)
```

## Migration Guide

### Step 1: Update Direct Council Creation

If you have code that creates councils directly:

```python
# Old code (no longer supported)
council = Council(name="my_council", agents=agents)

# New code - use factory
factory = CouncilFactory()
council = factory.create_council(name="my_council", agents=agents)
```

### Step 2: Extract Dependencies for Testing

For better testability, use custom dependencies:

```python
# Create custom dependencies
deps = CouncilDependencies(
    event_emitter=MockEventEmitter(),
    output_manager=MockOutputManager()
)

# Use factory with custom dependencies
factory = CouncilFactory(dependencies=deps)
council = factory.create_council(name="my_council", agents=agents)
```

### Step 3: Use Factory for Multiple Councils

If creating multiple councils:

```python
# Use factory
factory = CouncilFactory()

councils = [
    factory.create_council(name=f"council_{i}", agents=agents)
    for i in range(5)
]
```

### Step 4: Mock Dependencies in Tests

Replace real dependencies with mocks:

```python
# In tests
def test_council_behavior():
    mock_deps = CouncilDependencies(
        event_emitter=MockEventEmitter(),
        output_manager=MockOutputManager()
    )
    
    council = Council(
        name="test",
        agents=[MockAgent("test")],
        dependencies=mock_deps
    )
    
    # Test without side effects
```

## Benefits

1. **Testability** - Easy to test with mock dependencies
2. **Flexibility** - Swap implementations without changing Council code
3. **Separation of Concerns** - Council focuses on orchestration, not creating dependencies
4. **SOLID Principles** - Follows Dependency Inversion Principle
5. **Consistency** - Enforces proper dependency management across the codebase

## Best Practices

1. **Use Factory for Consistency** - When creating multiple councils
2. **Mock in Tests** - Always use mocks for unit tests
3. **Custom Implementations** - Create custom implementations for special requirements
4. **Dependency Containers** - Group related dependencies in CouncilDependencies
5. **Factory Pattern** - Always use CouncilFactory to create Council instances