# Write Comprehensive Tests

Create a test suite ensuring reliability and correctness.

## Test Structure:
```
tests/
├── unit/
│   ├── test_council.py
│   ├── test_steps.py
│   ├── test_context.py
│   └── test_agents.py
├── integration/
│   ├── test_execution.py
│   ├── test_workflows.py
│   └── test_events.py
└── fixtures/
    └── mock_agents.py
```

## Unit Tests:

### test_council.py
- Council initialization (steps vs agents)
- Error strategy configuration
- Event handler registration
- Step validation

### test_steps.py
- Each step type execution
- Event emission
- Error handling
- Parallel execution verification
- Debate rounds and voting
- Work distribution strategies

### test_context.py
- Context initialization
- Memory management and limits
- Agent context forking
- Serialization/deserialization
- Context summarization
- Permission enforcement

### test_agents.py
- Agent wrapper functionality
- Context injection
- Agent cloning
- Human agent timeouts
- Tool compatibility

## Integration Tests:

### test_execution.py
- Full council execution
- Async parallel execution
- Error propagation
- Event streaming
- Decision protocols

### test_workflows.py
- Common workflow patterns
- Multi-step councils
- Human interaction
- Context flow between steps

## Test Utilities:

### Mock Agents:
```python
class MockAgent:
    def __init__(self, name: str, response: str):
        self.name = name
        self.response = response
        self.call_count = 0
    
    async def __call__(self, prompt: str) -> str:
        self.call_count += 1
        return self.response
```

### Event Collector:
```python
class EventCollector:
    def __init__(self):
        self.events = []
    
    async def collect(self, event: CouncilEvent):
        self.events.append(event)
```

## Key Test Scenarios:
1. Council completes successfully
2. Agent fails - test each error strategy
3. Human timeout - default response used
4. Large context - summarization triggered
5. Parallel execution - verify concurrency
6. Vote tie - tiebreaker invoked
7. Context persistence - save/load cycle

## Performance Tests:
- Measure overhead vs direct agent calls
- Test with 10, 20, 50 agents
- Memory usage with large contexts
- Event streaming performance

## Coverage Goals:
- Unit test coverage >90%
- All error paths tested
- All event types verified
- Human interaction paths covered

## Commit Strategy for Tests
Tests should be committed with their corresponding features:

```bash
# Tests are committed WITH the feature they test
# See individual implementation commands for examples

# For test improvements or bug fixes:
git add tests/unit/test_specific.py
git commit -m "test: improve coverage for [feature]

- Add edge case tests for [scenario]
- Test error handling in [situation]
- Verify async behavior
- Increase coverage to X%"

# For test refactoring:
git commit -m "refactor(tests): simplify test fixtures

- Extract common mock agents to fixtures
- Reduce test duplication
- Improve test readability"
```

**Best Practice**: Always run the full test suite before committing:
```bash
uv run pytest --cov=konseho --cov-report=term-missing
```