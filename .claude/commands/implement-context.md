# Implement Context Management

Create the context system for sharing state between agents and steps.

## TDD Approach:

### 1. Write Tests First
```python
# tests/unit/test_context.py
import pytest
from konseho.core.context import CouncilContext, AgentContext

def test_context_initialization():
    """Context initializes with empty stores"""
    context = CouncilContext()
    assert context.shared_memory == {}
    assert context.step_results == []
    assert context.messages == []
    assert context.max_history == 100

def test_context_message_windowing():
    """Context maintains sliding window of messages"""
    context = CouncilContext(max_history=3)
    for i in range(5):
        context.add_message("user", f"message {i}")
    
    assert len(context.messages) == 3
    assert context.messages[0]["content"] == "message 2"

def test_agent_context_permissions():
    """Agent context enforces read/write permissions"""
    parent = CouncilContext()
    parent.shared_memory["test"] = "value"
    
    agent_ctx = parent.fork_for_agent("agent1")
    
    # Should be able to read allowed fields
    assert agent_ctx.read("shared_memory")["test"] == "value"
    
    # Should not be able to read restricted fields
    with pytest.raises(PermissionError):
        agent_ctx.read("restricted_field")

def test_context_serialization():
    """Context can be saved and restored"""
    context = CouncilContext()
    context.shared_memory["key"] = "value"
    context.add_message("user", "test message")
    
    # Serialize
    json_str = CouncilContextSerializer.to_json(context)
    
    # Deserialize
    restored = CouncilContextSerializer.from_json(json_str)
    assert restored.shared_memory["key"] == "value"
    assert restored.messages[0]["content"] == "test message"
```

### 2. Research Strands Message Format
Before implementing, understand how Strands handles messages:

#### If you have Strands MCP server:
```
mcp_strands_agents_mcp_server:quickstart
```

#### Key questions to answer:
- What is the message format? (likely {"role": "...", "content": "..."})
- How is conversation history passed to agents?
- Can agents be initialized with existing message history?
- Are there special message roles (system, user, assistant)?

#### Expected pattern:
```python
# Strands likely uses a format similar to:
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]

# And agents might accept history like:
agent = Agent(model="...", messages=messages)
```

### 3. Run Tests (Should Fail)
```bash
pytest tests/unit/test_context.py -v
```

### 4. Implement Context Classes
Build the minimal implementation to pass tests.

### 5. Commit Your Work
```bash
# Quality checks
uv run black src tests
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit/test_context.py

# Commit context implementation
git add konseho/core/context.py tests/unit/test_context.py
git commit -m "feat(core): implement context management system

- Add CouncilContext for shared state management
- Implement message history with sliding window
- Add AgentContext with permission-based access control
- Support context serialization/deserialization
- Include automatic summarization for large contexts
- Ensure thread-safe operations for parallel execution"
```

**Important**: Make sure context operations are thread-safe since multiple agents may access context concurrently.

## CouncilContext Class:
```python
class CouncilContext:
    def __init__(self, max_history: int = 100):
        self.shared_memory = {}  # Key-value store
        self.step_results = []   # Results from each step
        self.decisions = []      # Decision history
        self.messages = []       # For Strands compatibility
        self.proposals = {}      # Current step proposals
        self.critiques = {}      # Debate critiques
```

## Key Features:

### 1. Memory Management
- Automatic summarization when context grows large
- Sliding window for message history
- Scope-based storage (global vs step-local)

### 2. Agent Context Views
- Fork context for each agent with permissions
- Read-only: decisions, step_results
- Read-write: proposals, shared_memory
- Agent-specific filtering of relevant data

### 3. Context Flow
- Prepare step-specific context before execution
- Filter by domain for ParallelStep
- Full context for DebateStep (fairness)
- Work analysis for SplitStep

### 4. Persistence
- JSON serialization/deserialization
- Save/restore between sessions
- Compress large contexts

## Integration with Strands:
- Initialize Strands agents with context.messages
- Inject context into agent prompts
- Update shared memory with agent findings

## Helper Methods:
- get_step_context(step_name) -> filtered context
- fork_for_agent(agent_id) -> AgentContext
- add_message(role, content) -> manage history
- summarize_and_truncate() -> compress old messages