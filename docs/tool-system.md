# Tool System Overview

Konseho provides a comprehensive tool system that enables agents to interact with external systems, perform file operations, execute code, and more.

## Key Features

- **Parallel Tool Execution**: Built-in support for executing the same tool multiple times in parallel
- **Automatic Deduplication**: Prevents redundant work when using parallel execution
- **MCP Integration**: Full support for Model Context Protocol servers
- **Tool Collections**: Group related tools for easy management
- **Inline Diffs**: Visual feedback for file modifications
- **Provider Abstraction**: Pluggable implementations for external services

## Tool Categories

### Built-in Tools

Konseho includes several built-in tool categories:

#### File Operations (`konseho.tools.file_ops`)
- `file_read`: Read file contents with binary detection
- `file_write`: Write/overwrite files with automatic diff display
- `file_append`: Append content to existing files
- `file_list`: List directory contents
- `file_delete`: Remove files

#### Code Manipulation (`konseho.tools.code_ops`)
- `code_edit`: Replace code blocks with context awareness
- `code_insert`: Insert code at specific line numbers
- `code_search`: Search for patterns in code
- `code_refactor`: Automated refactoring operations

#### Shell Execution (`konseho.tools.shell_ops`)
- `shell_run`: Execute shell commands with timeout support
- `shell_stream`: Stream command output in real-time

#### HTTP Operations (`konseho.tools.http_ops`)
- `http_get`: Make HTTP GET requests
- `http_post`: Make HTTP POST requests with JSON/form data
- `http_download`: Download files from URLs

#### Search Operations (`konseho.tools.search_ops`)
- `web_search`: Pluggable web search with provider abstraction
- Built-in providers: Mock, Tavily, Brave Search, etc.

### MCP Tools

Any MCP server can provide tools to Konseho agents. See the [MCP Integration Guide](./mcp-integration.md) for details.

## Parallel Tool Execution

Every agent in Konseho has built-in parallel tool execution capability:

```python
from konseho import Agent

agent = Agent("Researcher", "You research topics thoroughly")

# Use the built-in parallel tool
results = await agent.parallel(
    tool_name="web_search",
    args_list=[
        {"query": "konseho multi-agent framework"},
        {"query": "AI agent orchestration"},
        {"query": "LLM tool use patterns"}
    ]
)
```

### Deduplication

The parallel executor automatically deduplicates work:

```python
# These will only execute 2 unique searches
results = await agent.parallel(
    tool_name="file_read",
    args_list=[
        {"path": "/tmp/file1.txt"},
        {"path": "/tmp/file2.txt"},
        {"path": "/tmp/file1.txt"},  # Duplicate - cached
        {"path": "/tmp/file2.txt"}   # Duplicate - cached
    ]
)
```

## Creating Custom Tools

### Basic Tool Creation

```python
from konseho.tools import tool

@tool
def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Add to agent
agent = Agent("Mathematician", "You solve math problems", tools=[calculate_fibonacci])
```

### Tools with Side Effects

```python
@tool
def send_notification(message: str, channel: str = "general") -> dict:
    """Send a notification to a Slack channel."""
    # Implementation here
    return {"success": True, "timestamp": "2024-01-01T12:00:00Z"}
```

### Async Tools

```python
@tool
async def fetch_data(url: str) -> dict:
    """Fetch data from an API asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## Tool Collections

Group related tools for easy management:

```python
from konseho.tools import ToolCollection

# Create a collection
data_tools = ToolCollection("Data Processing")
data_tools.add(read_csv)
data_tools.add(write_csv)
data_tools.add(analyze_dataframe)

# Add all tools to an agent
agent = Agent("Data Analyst", "You analyze data", tools=data_tools.tools)
```

## Provider Pattern

For tools that interact with external services, use the provider pattern:

```python
from abc import ABC, abstractmethod

class TranslationProvider(ABC):
    @abstractmethod
    def translate(self, text: str, source: str, target: str) -> str:
        pass

class GoogleTranslateProvider(TranslationProvider):
    def translate(self, text: str, source: str, target: str) -> str:
        # Implementation using Google Translate API
        pass

# Create tool with provider
provider = GoogleTranslateProvider(api_key="...")

@tool
def translate_text(text: str, source: str = "auto", target: str = "en") -> str:
    """Translate text between languages."""
    return provider.translate(text, source, target)
```

## Inline Diffs

File and code manipulation tools show inline diffs by default:

```python
# When modifying a file
result = file_write("/tmp/config.json", new_config, show_diff=True)

# Output includes colorized diff:
# --- config.json
# +++ config.json
# @@ -1,3 +1,3 @@
#  {
# -  "debug": false,
# +  "debug": true,
#    "port": 8080
#  }
```

## Best Practices

### 1. Tool Naming
- Use clear, descriptive names
- Follow naming conventions (verb_noun)
- Avoid abbreviations

### 2. Error Handling
```python
@tool
def risky_operation(path: str) -> dict:
    """Perform operation with proper error handling."""
    try:
        # Operation here
        return {"success": True, "result": data}
    except FileNotFoundError:
        return {"success": False, "error": "File not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 3. Input Validation
```python
@tool
def process_data(data: list, threshold: float = 0.5) -> dict:
    """Process data with validation."""
    if not isinstance(data, list):
        raise ValueError("Data must be a list")
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")
    # Process data
```

### 4. Documentation
Always provide clear docstrings:
```python
@tool
def analyze_sentiment(text: str, model: str = "default") -> dict:
    """
    Analyze sentiment of the given text.
    
    Args:
        text: The text to analyze
        model: Model to use ('default', 'advanced', 'multilingual')
        
    Returns:
        Dictionary with 'sentiment' (positive/negative/neutral) and 'confidence' (0-1)
    """
```

## Performance Considerations

### 1. Use Parallel Execution
When performing multiple independent operations:
```python
# Good - parallel execution
results = await agent.parallel("web_search", [
    {"query": q} for q in queries
])

# Less efficient - sequential
results = []
for query in queries:
    results.append(await web_search(query))
```

### 2. Cache Expensive Operations
```python
from functools import lru_cache

@tool
@lru_cache(maxsize=100)
def expensive_calculation(input_data: str) -> dict:
    """Cache results of expensive calculations."""
    # Expensive operation here
```

### 3. Set Appropriate Timeouts
```python
@tool
def long_running_task(data: str, timeout: int = 30) -> dict:
    """Task with configurable timeout."""
    # Implementation with timeout
```

## Security Considerations

### 1. Path Validation
```python
@tool
def safe_file_read(path: str) -> str:
    """Read file with path validation."""
    # Resolve to absolute path
    abs_path = os.path.abspath(path)
    
    # Check if within allowed directory
    if not abs_path.startswith(ALLOWED_DIR):
        raise ValueError("Access denied: Path outside allowed directory")
    
    return file_read(abs_path)
```

### 2. Input Sanitization
```python
@tool
def execute_query(query: str) -> list:
    """Execute database query with sanitization."""
    # Use parameterized queries
    # Validate query structure
    # Limit result size
```

### 3. Rate Limiting
```python
from konseho.tools.utils import rate_limit

@tool
@rate_limit(calls=10, period=60)  # 10 calls per minute
def api_request(endpoint: str) -> dict:
    """Make API request with rate limiting."""
    # Implementation
```

## Examples

See the following examples for practical implementations:
- `/examples/tools_example.py` - Basic tool usage
- `/examples/parallel_tools_example.py` - Parallel execution patterns
- `/examples/mcp_tools_example.py` - MCP integration
- `/examples/custom_tools_example.py` - Creating custom tools

## Integration with Personas

Tools can be attached to personas for reuse:

```python
from konseho import PersonaTemplate, PersonaRegistry

# Create persona with specific tools
coder_persona = PersonaTemplate(
    name="Senior Developer",
    instructions="You write clean, tested code",
    tools=[file_read, file_write, code_edit, shell_run]
)

# Register and use
registry = PersonaRegistry()
registry.register(coder_persona)

# Create agents from persona
dev1 = registry.create_agent("Senior Developer")
dev2 = registry.create_agent("Senior Developer")
```

Both agents will have the same tool set but maintain independent state.

## Summary

The Konseho tool system provides:
1. **Flexibility**: Use built-in tools, create custom tools, or integrate MCP servers
2. **Performance**: Automatic parallel execution and deduplication
3. **Usability**: Inline diffs, progress tracking, and clear error messages
4. **Extensibility**: Provider pattern for pluggable implementations
5. **Safety**: Built-in validation and error handling

This comprehensive tool system enables agents to interact effectively with their environment while maintaining clean, testable code.