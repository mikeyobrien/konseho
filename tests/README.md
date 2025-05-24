# Konseho Test Suite

This directory contains comprehensive tests for the Konseho SDK, ensuring reliability and correctness of all components.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_council.py     # Council initialization, execution, error handling
│   ├── test_steps.py       # ParallelStep, DebateStep, SplitStep functionality
│   ├── test_context.py     # Context management, history, serialization
│   └── test_agents.py      # Agent wrappers and human agent
├── integration/            # Integration tests for full workflows
│   ├── test_execution.py   # Council execution flows, async behavior
│   ├── test_workflows.py   # Common multi-agent patterns
│   └── test_events.py      # Event system and handlers
└── fixtures/               # Test utilities and mock objects
    ├── __init__.py
    └── mock_agents.py      # Mock agents for testing without Strands dependency
```

## Test Coverage

### Unit Tests

- **Council Tests** (`test_council.py`)
  - Initialization with various configurations
  - Step validation
  - Error strategies (halt, continue, retry)
  - Event handler registration
  - Context accumulation

- **Step Tests** (`test_steps.py`)
  - ParallelStep: concurrent execution, task splitting
  - DebateStep: proposal generation, voting strategies, moderator support
  - SplitStep: dynamic agent creation, auto-scaling
  - Custom step implementation

- **Context Tests** (`test_context.py`)
  - Initialization and data management
  - History tracking
  - Result storage
  - Prompt context generation with truncation
  - Serialization support

- **Agent Tests** (`test_agents.py`)
  - Agent wrapper functionality
  - Async execution
  - History tracking
  - Human agent with custom input handlers

### Integration Tests

- **Execution Tests** (`test_execution.py`)
  - Full council execution flows
  - Multi-step councils
  - Context flow between steps
  - Error handling strategies
  - AsyncExecutor for parallel councils

- **Workflow Tests** (`test_workflows.py`)
  - Research → Synthesis → Review workflow
  - Code analysis and review workflow
  - Brainstorm → Refine → Decide workflow
  - Human-in-the-loop patterns
  - Dynamic scaling workflows
  - Iterative refinement
  - Consensus building

- **Event Tests** (`test_events.py`)
  - Council lifecycle events
  - Error event emission
  - Async event handlers
  - Event data integrity
  - Multiple council isolation

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/konseho --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_council.py -v

# Run specific test
pytest tests/unit/test_council.py::TestCouncil::test_council_initialization -v

# Run tests matching pattern
pytest tests/ -k "error_handling" -v
```

## Mock Utilities

The `fixtures/mock_agents.py` module provides:

- `MockStrandsAgent`: Simulates Strands agent behavior
- `MockAgent`: Async mock agent with failure simulation
- `EventCollector`: Collects and validates events
- `CouncilEvent`: Event data structure for testing

These mocks allow testing without external dependencies.

## Key Test Scenarios

1. **Success Paths**
   - Council completes all steps successfully
   - Agents work in parallel
   - Context flows between steps
   - Events are emitted correctly

2. **Error Handling**
   - Agent failures with different strategies
   - Human timeouts
   - Event handler errors
   - Council error propagation

3. **Performance**
   - Parallel execution verification
   - Large context handling
   - Multiple council concurrency
   - Event streaming performance

4. **Edge Cases**
   - Empty councils
   - Vote ties in debates
   - Context size limits
   - Mismatched council/task counts

## Coverage Goals

- Unit test coverage: >90%
- All error paths tested
- All event types verified
- Human interaction paths covered
- Async behavior validated