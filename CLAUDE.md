# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Konseho is a Python SDK for creating multi-agent "councils" built on top of the Strands Agent SDK. It enables specialized AI agents to work together through debate, parallel execution, and coordinated workflows to accomplish complex tasks with better context management.

## Development Commands

### Environment Setup
```bash
# Set up development environment with dependencies
./setup-dev.sh
```

### Running the Project
```bash
# Run the main module
./run.sh
# Or directly:
uv run python -m konseho
```

### Development Tasks
```bash
# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_main.py::test_specific

# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src

# Run all quality checks
uv run black src tests && uv run ruff check src tests && uv run mypy src && uv run pytest
```

## Architecture Overview

### Core Concepts

1. **Council**: The main orchestrator that manages multiple agents working together through defined steps
2. **Steps**: Different execution patterns for agent coordination:
   - `DebateStep`: Agents propose competing solutions and vote
   - `ParallelStep`: Agents work on different domains simultaneously
   - `SplitStep`: Dynamically distributes work across multiple agent instances
3. **Context Management**: Shared memory and state that flows between agents and steps
4. **Agent Wrappers**: Integration layer between Strands agents and the council system

### Key Design Patterns

- **Orchestrated Debate**: Moderator assigns tasks → Parallel proposals → Structured debate → Voting/consensus → Synthesized output
- **Context Accumulation**: Each step builds on previous findings with managed context windows
- **Event-Driven Architecture**: All operations emit events for observability and real-time UI updates
- **Human-in-the-Loop**: Humans can participate as specialized agents at any step

### Planned Project Structure
```
konseho/
├── core/           # Council, Steps, Context management
├── agents/         # Agent wrappers and human integration
├── execution/      # Async execution engine and events
└── interface/      # Terminal chat interface
```

## Development Guidelines

When implementing features:
1. Follow the async/await pattern throughout for parallel execution capabilities
2. Ensure all steps emit proper events for the terminal interface
3. Maintain the <10 lines of code goal for basic council creation
4. Include comprehensive type hints and docstrings
5. Handle errors gracefully with the configured strategy (halt/continue/retry)

### Core Development Principles

**KISS (Keep It Simple, Stupid)**
- Start with the simplest implementation that works
- Avoid premature optimization or over-engineering
- If a feature can be implemented in 10 lines instead of 100, choose the simpler approach
- Complex abstractions should only be added when proven necessary

**YAGNI (You Aren't Gonna Need It)**
- Don't implement features until they are actually needed
- Avoid building "just in case" functionality
- Focus on current requirements, not hypothetical future needs
- Remove unused code promptly

**SOLID Principles**
- **Single Responsibility**: Each class/function should have one clear purpose
  - Council manages workflow, not agent internals
  - Steps handle execution patterns, not context management
  - Context manages state, not execution logic
- **Open/Closed**: Design for extension without modification
  - New step types should extend Step base class
  - New error strategies shouldn't require changing existing code
- **Liskov Substitution**: All Step subclasses must be interchangeable
- **Interface Segregation**: Keep interfaces focused and minimal
  - Agents only need `work_on()` method
  - Steps only need `execute()` method
- **Dependency Inversion**: Depend on abstractions (Strands Agent interface) not concrete implementations

### Practical Examples
```python
# GOOD: Simple, focused, extensible
class Step:
    async def execute(self, task: str, context: Context) -> Result:
        raise NotImplementedError

# BAD: Trying to do too much
class Step:
    async def execute_with_retry_and_logging_and_metrics_and_caching(...):
        # 200 lines of mixed concerns
```

## Idiomatic Python & Type Hints

### Python Style Guidelines

**Use Pythonic idioms and patterns:**
```python
# GOOD: Pythonic approaches
# List comprehensions for simple transformations
results = [agent.name for agent in agents if agent.is_active]

# Generator expressions for memory efficiency
total = sum(len(result) for result in results)

# Context managers for resource handling
async with council.session() as session:
    result = await session.execute(task)

# Enumerate for index access
for i, agent in enumerate(agents):
    print(f"Agent {i}: {agent.name}")

# BAD: Non-pythonic patterns
# Manual index tracking
i = 0
for agent in agents:
    print(f"Agent {i}: {agent.name}")
    i += 1
```

**Prefer composition over inheritance:**
```python
# GOOD: Composition with clear interfaces
class Council:
    def __init__(self, executor: Executor, context: Context):
        self._executor = executor
        self._context = context

# BAD: Deep inheritance hierarchies
class AdvancedDebateCouncil(DebateCouncil, ParallelCouncil, BaseCouncil):
    pass
```

### Type Hint Requirements

**Always use type hints for:**
- All function/method parameters and return values
- Class attributes
- Module-level variables

**Type hint examples:**
```python
from typing import List, Dict, Optional, Union, TypeVar, Protocol
from collections.abc import Sequence, Mapping

# Basic types
def process_task(task: str, priority: int = 1) -> bool:
    return True

# Collections with generics
async def gather_results(agents: List[Agent]) -> Dict[str, str]:
    return {agent.name: await agent.work_on(task) for agent in agents}

# Optional types
def find_agent(name: str) -> Optional[Agent]:
    return agents.get(name)

# Union types (prefer | operator for Python 3.10+)
def parse_input(data: str | bytes) -> dict:
    return json.loads(data)

# Generic type variables
T = TypeVar('T')
def first_or_none(items: Sequence[T]) -> Optional[T]:
    return items[0] if items else None

# Protocol for structural typing
class Workable(Protocol):
    async def work_on(self, task: str) -> str: ...

# Complex nested types
ConfigDict = Dict[str, Union[str, int, Dict[str, str]]]
```

**Type hint constraints:**
- Use `from __future__ import annotations` for forward references
- Prefer `list[T]` over `List[T]` in Python 3.9+
- Use `TypeAlias` for complex repeated types
- Avoid `Any` unless absolutely necessary
- Use `Protocol` for duck typing interfaces
- Use `TypedDict` for structured dictionaries

```python
from __future__ import annotations
from typing import TypeAlias, TypedDict, Protocol

# Type aliases for clarity
AgentResults: TypeAlias = dict[str, str]

# Typed dictionaries for structured data
class StepConfig(TypedDict):
    name: str
    timeout: int
    retry_count: int

# Protocols for interfaces
class Executable(Protocol):
    async def execute(self, task: str, context: Context) -> Result: ...
```

## Testing Approach

- Use mock Strands agents for unit tests to avoid external dependencies
- Create integration tests with simple agents for end-to-end validation
- Test async execution patterns thoroughly
- Benchmark parallel execution performance

## Claude 4 Best Practices for Tool Calling & Agentic Coding

### Parallel Tool Execution
For maximum efficiency, whenever you need to perform multiple independent operations, invoke all relevant tools simultaneously rather than sequentially. This is especially important for:
- Running multiple tests or checks
- Searching across different files or patterns
- Fetching data from multiple sources
- Performing batch file operations

Example:
```python
# When implementing features that require multiple file operations:
# DO: Execute independent reads/searches in parallel
# DON'T: Chain operations unnecessarily
```

### File Management
- Minimize temporary file creation during development tasks
- If you create any temporary new files, scripts, or helper files for iteration, clean up these files by removing them at the end of the task
- Prefer in-memory operations when possible
- Use existing test fixtures rather than creating new temporary test files

### Thoughtful Tool Usage
After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. This helps:
- Avoid redundant operations
- Choose the most efficient approach
- Maintain clean project structure
- Ensure all changes align with project patterns

### Context-Aware Development
When working with the Konseho codebase:
- Leverage the event-driven architecture for parallel agent execution
- Use the existing step patterns (DebateStep, ParallelStep, SplitStep) effectively
- Maintain the simplicity goals (<10 lines for basic council creation)
- Follow the established async/await patterns throughout