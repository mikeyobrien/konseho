# Implement Execution Engine

Build the async execution system with event streaming.

## TDD Approach:

### 1. Research Strands Execution Patterns
Understand how Strands handles execution:

#### If you have Strands MCP server:
```
mcp_strands_agents_mcp_server:quickstart
mcp_strands_agents_mcp_server:model_providers
```

#### Key patterns to determine:
1. **Sync vs Async**:
   - Is `agent("prompt")` synchronous or async?
   - Do we need `await agent("prompt")` or just `agent("prompt")`?

2. **Multiple Agent Coordination**:
   - Can we run multiple agents in parallel?
   - Any built-in orchestration support?

3. **Expected patterns**:
   ```python
   # Synchronous (likely):
   response = agent("prompt")
   
   # Or Asynchronous:
   response = await agent("prompt")
   
   # For parallel execution, we'll likely need:
   import asyncio
   results = await asyncio.gather(
       agent1("task1"),
       agent2("task2")
   )
   ```

### 2. Write Tests First
```python
# tests/unit/test_execution.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_parallel_execution_timing():
    """Verify agents execute in parallel, not sequentially"""
    execution_times = []
    
    async def timed_agent(name, delay):
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(delay)
        execution_times.append((name, start))
        return f"{name} done"
    
    executor = StepExecutor()
    agents = {
        "fast": lambda t: timed_agent("fast", 0.1),
        "slow": lambda t: timed_agent("slow", 0.2)
    }
    
    start = asyncio.get_event_loop().time()
    results = await executor.execute_parallel(agents, "task", Mock())
    total_time = asyncio.get_event_loop().time() - start
    
    # Should complete in ~0.2s (parallel) not 0.3s (sequential)
    assert total_time < 0.25
    assert len(results) == 2
    
    # Verify both started at approximately the same time
    assert abs(execution_times[0][1] - execution_times[1][1]) < 0.01

@pytest.mark.asyncio
async def test_event_ordering():
    """Events from parallel execution maintain correct order"""
    events = []
    
    async def event_handler(event):
        events.append(event)
    
    executor = StepExecutor(event_handler=event_handler)
    # Test implementation
    
    # Verify events are properly ordered
    assert events[0].type == EventType.STEP_STARTED
    assert all(e.type == EventType.AGENT_WORKING for e in events[1:3])
    assert events[-1].type == EventType.STEP_COMPLETED

@pytest.mark.asyncio
async def test_error_handling_strategies():
    """Test each error strategy behavior"""
    failing_agent = AsyncMock(side_effect=Exception("Agent failed"))
    
    # Test halt strategy
    executor = StepExecutor(error_strategy="halt")
    with pytest.raises(StepExecutionError):
        await executor.execute_step(Mock(agents=[failing_agent]), "task", Mock())
    
    # Test continue strategy
    executor = StepExecutor(error_strategy="continue")
    result = await executor.execute_step(Mock(agents=[failing_agent]), "task", Mock())
    assert result.status == "partial"
    
    # Test retry strategy
    executor = StepExecutor(error_strategy="retry", retry_attempts=2)
    failing_agent.call_count = 0
    with pytest.raises(StepExecutionError):
        await executor.execute_step(Mock(agents=[failing_agent]), "task", Mock())
    assert failing_agent.call_count == 3  # Initial + 2 retries
```

### 3. Run Tests (Should Fail)
```bash
pytest tests/unit/test_execution.py -v
```

### 4. Implement Execution Engine
Build incrementally to pass each test.

## StepExecutor Class:
```python
class StepExecutor:
    async def execute_step(self, step: Step, task: str, context: CouncilContext) -> StepResult:
        # Prepare step context
        # Execute based on step type
        # Handle parallelization
        # Emit events
        # Return results
```

## Execution Patterns:

### 1. Parallel Execution (ParallelStep)
```python
async def execute_parallel(agents: Dict[str, Agent], task: str):
    tasks = [
        agent.work_on(f"{task} for {domain}", context)
        for domain, agent in agents.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. Debate Orchestration (DebateStep)
- Gather initial proposals in parallel
- Conduct debate rounds sequentially
- Each agent sees others' proposals
- Vote/consensus after final round

### 3. Dynamic Distribution (SplitStep)
- Analyze task to identify work items
- Create agent pool dynamically
- Distribute work with strategy
- Merge results intelligently

## Event System:

### Event Types:
```python
class EventType(Enum):
    COUNCIL_STARTED = "council_started"
    STEP_STARTED = "step_started"
    AGENT_WORKING = "agent_working"
    PROPOSAL_MADE = "proposal_made"
    DEBATE_ROUND = "debate_round"
    DECISION_MADE = "decision_made"
    STEP_COMPLETED = "step_completed"
    ERROR_OCCURRED = "error_occurred"
```

### Event Streaming:
- Emit events in real-time
- Buffer events from parallel execution
- Maintain event ordering
- Support multiple observers

## Error Handling:
- Capture agent failures
- Apply error strategy
- Emit error events
- Provide degraded results
- Support retry with backoff

## Decision Protocols:
- Simple majority voting
- Weighted voting by expertise
- Consensus with threshold
- Moderator synthesis

## Commit Your Work
```bash
# Quality checks
uv run black src tests
uv run ruff check src tests  
uv run mypy src
uv run pytest tests/unit/test_execution.py

# Commit execution engine
git add konseho/execution/executor.py tests/unit/test_execution.py
git commit -m "feat(execution): implement async execution engine

- Add StepExecutor with true parallel execution
- Implement event streaming for real-time updates
- Support multiple error handling strategies
- Include decision protocols (voting, consensus)
- Verify parallelism with timing tests
- Ensure proper event ordering from concurrent operations"

# Commit event system separately
git add konseho/execution/events.py
git commit -m "feat(execution): add comprehensive event system

- Define EventType enum for all council events
- Implement CouncilEvent with metadata support
- Add event buffering for parallel execution
- Support multiple event observers
- Include event filtering and routing"
```

**Performance Note**: Profile the execution engine to ensure minimal overhead compared to direct agent calls.