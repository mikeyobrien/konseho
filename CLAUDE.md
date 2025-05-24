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
python -m src.konseho
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

## Testing Approach

- Use mock Strands agents for unit tests to avoid external dependencies
- Create integration tests with simple agents for end-to-end validation
- Test async execution patterns thoroughly
- Benchmark parallel execution performance