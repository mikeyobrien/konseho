# Implement Agent Integration

Create the agent wrapper system for Strands integration and human participation.

## Important: Research Strands Agent SDK
Before implementing, understand the Strands Agents SDK:

### If you have Strands MCP server:
```
mcp_strands_agents_mcp_server:quickstart
mcp_strands_agents_mcp_server:agent_tools
```

### Key areas to understand:
1. **Agent Creation**: 
   - Constructor parameters (model, tools, prompts)
   - The `Agent()` class from strands
   
2. **Tool Integration**:
   - How to use @tool decorator
   - Tool function signatures
   - Tool descriptions for agent use

3. **Agent Execution**:
   - Is agent() call async or sync?
   - Message format and parameters
   - Conversation history management

4. **Model Providers**:
   - How different providers are configured
   - Environment variables needed

### Example patterns to look for:
```python
from strands import Agent, tool

@tool
def my_tool(param: str) -> str:
    """Tool description"""
    return result

agent = Agent(model="gpt-4", tools=[my_tool])
response = agent("prompt")
```

## CouncilAgent Wrapper:
```python
class CouncilAgent:
    def __init__(self, strands_agent: Agent, role: str):
        self.agent = strands_agent
        self.role = role
        self.id = f"{role}_{uuid4()}"
    
    async def work_on(self, task: str, context: AgentContext) -> str:
        # Inject context into prompts
        # Call Strands agent
        # Update context with findings
```

## Key Features:

### 1. Context Injection
- Prepend relevant context to agent prompts
- Include previous step results
- Add shared memory relevant to agent's domain
- Maintain conversation continuity

### 2. Agent Cloning
- For SplitStep dynamic agent creation
- Preserve base configuration
- Unique IDs for tracking
- Independent message histories

### 3. Tool Compatibility
- Pass through Strands tools unchanged
- Add council-specific tools if needed
- Handle tool errors gracefully

## HumanAgent Implementation:

### Features:
- Async input with timeouts
- Context display formatting
- Different interaction modes:
  - Reviewer: approve/reject/modify
  - Expert: provide domain knowledge
  - Tiebreaker: resolve voting deadlocks
  - Validator: safety checks

### Interface:
- Clear visual indicators for input needed
- Show relevant context concisely
- Progress indicators during wait
- Timeout handling with defaults

## Example Agents:
Create templates in examples/agents/:
- SimpleAnalyzer: Basic text analysis
- CodeExplorer: Codebase navigation
- TaskPlanner: Task decomposition
- Coder: Implementation
- Reviewer: Quality checks

## Commit Your Work
```bash
# Quality checks
uv run black src tests
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit/test_agents.py

# Commit agent wrappers
git add konseho/agents/base.py tests/unit/test_agents.py
git commit -m "feat(agents): implement Strands agent wrapper for councils

- Add CouncilAgent wrapper with context injection
- Implement agent cloning for dynamic creation
- Support message history synchronization
- Maintain compatibility with Strands tools
- Include tests with mock Strands agents"

# Commit human agent separately
git add konseho/agents/human.py
git commit -m "feat(agents): add human-in-the-loop agent support

- Implement HumanAgent with async input handling
- Add configurable timeouts with graceful fallbacks
- Support multiple human roles (reviewer, expert, validator)
- Include clear visual indicators for input requests
- Add tests for timeout scenarios"
```