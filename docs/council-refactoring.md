# Council Refactoring: Breaking the God Class

## Overview

The Council class has been refactored from a monolithic "God Class" into a composition of specialized components, each with a single responsibility. This improves maintainability, testability, and extensibility while preserving the existing API.

## Architecture Changes

### Before: Monolithic Council
```python
class Council:
    # 200+ lines handling:
    # - Step execution
    # - Error handling  
    # - Event emission
    # - Output management
    # - Moderator assignment
    # - Context management
```

### After: Composition of Components
```python
class Council:
    # Coordinates between:
    # - ErrorHandler (error strategies)
    # - StepOrchestrator (step execution)
    # - ModeratorAssigner (debate moderation)
    # - Dependencies (context, events, output)
```

## New Components

### 1. ErrorHandler
Manages all error handling strategies and retry logic.

```python
from konseho.core import ErrorHandler, ErrorStrategy

# Create with specific strategy
error_handler = ErrorHandler(
    error_strategy=ErrorStrategy.RETRY,
    max_retries=3,
    fallback_handler=custom_fallback_fn
)

# Strategies available:
# - HALT: Re-raise exceptions (default)
# - CONTINUE: Log and continue with next step
# - RETRY: Retry with exponential backoff
# - FALLBACK: Use custom fallback handler
```

### 2. StepOrchestrator
Handles sequential execution of steps with proper event emission.

```python
from konseho.core import StepOrchestrator

orchestrator = StepOrchestrator(
    steps=[step1, step2],
    event_emitter=event_emitter,
    output_manager=output_manager,
    error_handler=error_handler
)

# Execute all steps
results = await orchestrator.execute_steps(task, context)
```

### 3. ModeratorAssigner
Manages moderator assignment for debate steps.

```python
from konseho.core import ModeratorAssigner

assigner = ModeratorAssigner(default_moderator=agent1)

# Set a pool of moderators (round-robin assignment)
assigner.set_moderator_pool([agent1, agent2, agent3])

# Assign to all debate steps
assigner.assign_moderators(steps)

# Or assign specific moderator
assigner.assign_specific_moderator(debate_step, agent2)
```

## API Compatibility

The existing Council API remains unchanged:

```python
# Old code still works
council = CouncilFactory().create_council(
    name="my_council",
    steps=[...],
    error_strategy="retry"
)

result = await council.execute("task")
```

## Advanced Usage

### Custom Error Handling
```python
async def my_fallback(error, step, task, context):
    # Custom recovery logic
    return StepResult(
        step_name=step.name,
        output=f"Recovered from {error}",
        metadata={"fallback": True}
    )

council = Council(
    name="resilient_council",
    steps=[...],
    dependencies=deps,
    error_strategy="fallback"
)
council.set_fallback_handler(my_fallback)
```

### Moderator Management
```python
# Create moderator pool
moderators = [
    Agent(name="senior_mod", ...),
    Agent(name="technical_mod", ...),
    Agent(name="domain_mod", ...)
]

council.set_moderator_pool(moderators)
# Moderators assigned round-robin to debate steps
```

### Direct Component Access
```python
# Access components for advanced control
council._error_handler.max_retries = 5
council._moderator_assigner.set_moderator_pool([...])
council._step_orchestrator.event_emitter = custom_emitter
```

## Benefits

1. **Single Responsibility**: Each component has one clear purpose
2. **Testability**: Components can be tested in isolation  
3. **Extensibility**: Easy to add new error strategies or execution patterns
4. **Maintainability**: Smaller, focused classes are easier to understand
5. **Reusability**: Components can be used independently

## Migration Guide

No migration needed! The refactoring maintains full backward compatibility. However, you can now:

1. **Inject custom error handlers** for advanced error recovery
2. **Manage moderator pools** for better debate facilitation  
3. **Access internal components** for fine-grained control
4. **Test components individually** for better test coverage

## Examples

See `examples/advanced_council_components.py` for comprehensive examples of:
- Custom error handling strategies
- Moderator pool management
- Event-driven monitoring
- Programmatic step building
- Retry configuration