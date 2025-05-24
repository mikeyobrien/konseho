# Implement Step Classes

Create the step class hierarchy for different coordination patterns using Test-Driven Development.

## TDD Approach:

### 1. Write Tests First
```python
# tests/unit/test_steps.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_debate_step_proposals():
    """DebateStep gathers proposals from all agents"""
    agents = [AsyncMock(return_value="proposal1"), AsyncMock(return_value="proposal2")]
    step = DebateStep("debate", agents)
    result = await step.execute("task", Mock())
    
    assert all(agent.called for agent in agents)
    assert result.status == "success"
    assert len(result.agent_contributions) == 2

@pytest.mark.asyncio
async def test_parallel_step_execution():
    """ParallelStep executes agents concurrently"""
    # Mock agents with delays to verify parallelism
    import time
    start = time.time()
    
    async def slow_agent(task):
        await asyncio.sleep(0.1)
        return "done"
    
    agents = {"a": slow_agent, "b": slow_agent}
    step = ParallelStep("parallel", agents)
    await step.execute("task", Mock())
    
    # Should take ~0.1s (parallel) not ~0.2s (sequential)
    assert time.time() - start < 0.15

@pytest.mark.asyncio  
async def test_split_step_work_distribution():
    """SplitStep dynamically creates agents for work items"""
    agent_template = Mock()
    agent_template.clone = Mock(return_value=AsyncMock(return_value="result"))
    
    step = SplitStep("split", agent_template, split_by="files")
    # Mock work analysis to return 3 items
    step.analyze_and_split = AsyncMock(return_value=["file1", "file2", "file3"])
    
    result = await step.execute("task", Mock())
    assert agent_template.clone.call_count == 3
```

### 2. Run Tests (Should Fail)
```bash
pytest tests/unit/test_steps.py -v
```

### 3. Implement Step Classes
Implement just enough to make tests pass.

### 4. Commit Your Work
After implementing each step type:

```bash
# Quality checks
uv run black src tests
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit/test_steps.py

# Commit each step type separately for clarity
git add konseho/core/steps.py tests/unit/test_steps.py
git commit -m "feat(core): implement Step base class and DebateStep

- Add abstract Step base class with execute interface
- Implement DebateStep with proposal gathering and voting
- Support configurable debate rounds and decision methods
- Include async execution support
- Add comprehensive tests for debate flow"

# Then commit other step types
git commit -m "feat(core): implement ParallelStep for concurrent execution

- Add ParallelStep with domain-based agent mapping
- Implement true parallel execution with asyncio.gather
- Verify parallelism with timing tests
- Support flexible result merging"

git commit -m "feat(core): implement SplitStep for dynamic work distribution

- Add SplitStep with configurable splitting strategies
- Support dynamic agent cloning for work items
- Implement work analysis and distribution logic
- Include tests for various splitting scenarios"
```

## Base Step Class:
```python
class Step:
    def __init__(self, name: str, agents: List[Agent]):
        self.name = name
        self.agents = agents
    
    async def execute(self, task: str, context: CouncilContext) -> StepResult:
        raise NotImplementedError
```

## Step Types to Implement:

### 1. DebateStep
- Agents propose competing solutions
- Conduct debate rounds with critiques
- Vote or reach consensus
- Decision methods: vote, weighted_vote, consensus

### 2. ParallelStep
- Domain-based agent mapping (dict)
- Agents work simultaneously on different aspects
- Results merged into comprehensive output
- Example: {"frontend": UIAgent(), "backend": APIAgent()}

### 3. SplitStep
- Dynamic work distribution
- Strategies: by_files, by_functions, by_topics, auto
- Clone agent template for each work item
- Merge results intelligently

## Event Emission:
Each step must emit:
- step_started
- agent_working
- proposal_made (for debates)
- decision_made
- step_completed

## Error Handling:
- Wrap agent failures in StepExecutionError
- Support partial results for continue strategy
- Enable retry with exponential backoff