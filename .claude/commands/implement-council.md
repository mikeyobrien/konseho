# Implement Core Council Class

Implement the base Council class following the architecture design using Test-Driven Development.

## TDD Approach:

### 1. Write Tests First
```python
# tests/unit/test_council.py
def test_council_init_with_steps():
    """Council can be initialized with steps"""
    steps = [Mock(Step)]
    council = Council(steps=steps)
    assert council.steps == steps
    assert council.error_strategy == "halt"  # default

def test_council_init_with_agents():
    """Council can be initialized with just agents (creates DebateStep)"""
    agents = [Mock(Agent), Mock(Agent)]
    council = Council(agents=agents)
    assert len(council.steps) == 1
    assert isinstance(council.steps[0], DebateStep)

def test_council_execute_success():
    """Council executes steps in order"""
    # Test implementation here

def test_council_error_handling():
    """Council handles errors according to strategy"""
    # Test each error strategy
```

### 2. Run Tests (They Should Fail)
```bash
pytest tests/unit/test_council.py -v
# All tests should fail since Council doesn't exist yet
```

### 3. Implement Council Class
Now implement the minimal code to make tests pass.

### 4. Commit Your Work
Once tests are passing:

```bash
# Run all quality checks first
uv run black src tests
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit/test_council.py

# If all pass, commit with a descriptive message
git add konseho/core/council.py tests/unit/test_council.py
git commit -m "feat(core): implement Council class with basic step orchestration

- Add Council class with support for steps and agents initialization
- Implement execute() method for sequential step execution
- Add configurable error strategies (halt, continue, retry)
- Include comprehensive unit tests
- Follow SOLID principles with clear separation of concerns"
```

**Commit Guidelines**:
- Use conventional commits: feat(), fix(), test(), docs(), refactor()
- Keep commits focused on a single feature/fix
- Include both implementation and tests in the same commit
- Reference any related issues if applicable

## Requirements:
1. Support both simple (agents only) and complex (steps) initialization
2. Implement execute() method with proper orchestration
3. Add configurable error strategies: halt, continue, retry, fallback
4. Include event emission hooks for observability
5. Support both sync and async execution

## Example Usage Target:
```python
# Simple debate council (<10 lines)
council = Council([
    DebateStep("solve", [Explorer(), Planner(), Coder()])
])
result = council.execute("Fix the authentication bug")

# Multi-step parallel council
council = Council([
    ParallelStep("explore", {
        "code": CodeExplorer(),
        "tests": TestAnalyzer()
    }),
    DebateStep("plan", [Architect(), Designer()], rounds=2),
    SplitStep("implement", Coder(), split_by="files")
])
```

## Key Methods:
- __init__(steps=None, agents=None, workflow="sequential", error_strategy="halt")
- execute(task: str) -> CouncilResult
- stream_execute(task: str) -> AsyncIterator[CouncilEvent]
- handle_error(error: StepExecutionError, context: CouncilContext)