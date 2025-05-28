# Protocols Architecture

This document describes the protocol-based architecture introduced to improve loose coupling, testability, and extensibility in Konseho.

## Overview

Konseho now uses Python protocols (PEP 544) to define interfaces for core components. This enables:
- **Loose coupling** - Components depend on interfaces, not concrete implementations
- **Better testability** - Easy to create mock implementations for testing
- **Extensibility** - New implementations without modifying existing code
- **Type safety** - Runtime protocol checking and static type hints
- **Gradual migration** - Adapters allow incremental adoption

## Core Protocols

### IAgent Protocol

Defines the interface for all agent implementations:

```python
@runtime_checkable
class IAgent(Protocol):
    @property
    def name(self) -> str:
        """Agent's unique name."""
        
    @property
    def model(self) -> str:
        """Model identifier."""
        
    async def work_on(self, task: str) -> str:
        """Process a task and return result."""
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities and metadata."""
```

### IStep Protocol

Defines the interface for workflow steps:

```python
@runtime_checkable
class IStep(Protocol):
    @property
    def name(self) -> str:
        """Step name for identification."""
        
    async def execute(self, task: str, context: IContext) -> IStepResult:
        """Execute the step with given task and context."""
        
    def validate(self) -> List[str]:
        """Validate step configuration."""
```

### IContext Protocol

Defines the interface for context management:

```python
@runtime_checkable
class IContext(Protocol):
    def add(self, key: str, value: Any) -> None:
        """Add a key-value pair to context."""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context."""
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update context with multiple key-value pairs."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Export context as dictionary."""
        
    def get_size(self) -> int:
        """Get context size in bytes/tokens."""
```

## Using Protocols

### Creating Mock Implementations

For testing, you can create lightweight mock implementations:

```python
from konseho.protocols import IAgent
from konseho.adapters import MockAgent

# Use the provided MockAgent
mock = MockAgent("test-agent", response="Test response")

# Or create your own
class CustomMockAgent:
    def __init__(self, name: str):
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def model(self) -> str:
        return "mock-model"
    
    async def work_on(self, task: str) -> str:
        return f"Mock response for: {task}"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {"mock": True}

# Both implement IAgent
assert isinstance(mock, IAgent)
assert isinstance(CustomMockAgent("custom"), IAgent)
```

### Type Hints with Protocols

Use protocols in type hints for better flexibility:

```python
from typing import List
from konseho.protocols import IAgent, IStep, IContext

async def run_workflow(
    agents: List[IAgent],  # Accept any IAgent implementation
    steps: List[IStep],    # Accept any IStep implementation
    context: IContext      # Accept any IContext implementation
) -> str:
    """Workflow that works with any protocol implementations."""
    for step in steps:
        result = await step.execute("task", context)
        context.add(f"{step.name}_result", result.output)
    return "Complete"
```

### Migration with Adapters

Use adapters to wrap existing implementations:

```python
from konseho.agents.base import AgentWrapper
from konseho.adapters import AgentAdapter

# Existing agent
agent = AgentWrapper(strands_agent, "existing-agent")

# Wrap with adapter to ensure protocol compliance
adapted = AgentAdapter(agent)

# Now it implements IAgent
assert isinstance(adapted, IAgent)
```

## Benefits in Practice

### 1. Testing

Create isolated unit tests without external dependencies:

```python
def test_council_with_mocks():
    # Use mock agents instead of real API calls
    agents = [
        MockAgent("analyst", response="Analysis complete"),
        MockAgent("reviewer", response="Review complete")
    ]
    
    council = Council(agents=agents)
    result = council.run("Test task")
    
    # Fast, deterministic tests without API calls
    assert "Analysis complete" in str(result)
```

### 2. Alternative Implementations

Easily swap implementations:

```python
# Production: Use Strands agents
from konseho.agents.base import create_agent
agents = [await create_agent("prod-agent", "claude-3")]

# Testing: Use mock agents
agents = [MockAgent("test-agent")]

# Local development: Use custom implementation
class LocalAgent:
    # ... implement IAgent protocol ...
    
agents = [LocalAgent()]

# All work with the same Council code
council = Council(agents=agents)
```

### 3. Provider Abstraction

Support multiple providers through protocols:

```python
@runtime_checkable
class IModelProvider(Protocol):
    async def create_agent(self, name: str, model: str, **kwargs) -> IAgent:
        """Create an agent instance."""

# Different provider implementations
class OpenAIProvider:
    async def create_agent(self, name: str, model: str, **kwargs) -> IAgent:
        # Create OpenAI-based agent
        
class AnthropicProvider:
    async def create_agent(self, name: str, model: str, **kwargs) -> IAgent:
        # Create Anthropic-based agent

# Use any provider
provider: IModelProvider = OpenAIProvider()  # or AnthropicProvider()
agent = await provider.create_agent("agent", "gpt-4")
```

## Migration Strategy

1. **Phase 1** (Complete): Define protocols without breaking existing code
2. **Phase 2** (Complete): Add adapters for existing classes
3. **Phase 3**: Update type hints to use protocols where appropriate
4. **Phase 4**: Create provider abstractions for model/search providers
5. **Phase 5**: Refactor internal code to depend on protocols

## Best Practices

1. **Prefer protocols over concrete types** in function signatures
2. **Use runtime_checkable** for protocols that need isinstance() checks
3. **Keep protocols minimal** - only include essential methods
4. **Document protocol contracts** clearly
5. **Provide adapters** for backward compatibility

## Example: Full Protocol-Based Council

```python
from konseho.protocols import IAgent, IStep, IContext
from konseho.adapters import MockAgent, MockStep
from konseho.core.context import Context

# Create protocol-compliant components
agents: List[IAgent] = [
    MockAgent("researcher"),
    MockAgent("analyst"),
    MockAgent("writer")
]

steps: List[IStep] = [
    MockStep("research", "Research findings"),
    MockStep("analyze", "Analysis results"),
    MockStep("write", "Final report")
]

context: IContext = Context()

# Use in council (future implementation)
council = Council(
    agents=agents,
    steps=steps,
    context=context
)

result = await council.execute("Create market analysis")
```

This architecture provides a solid foundation for future extensibility while maintaining compatibility with existing code.