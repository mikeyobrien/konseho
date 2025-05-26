# Search Provider Architecture Summary

## Overview

Konseho provides a flexible search provider architecture that supports multiple integration methods:

1. **Mock/Fake Providers** - For testing without API keys
2. **MCP Server Integration** - Leverage MCP search servers (brave-search, tavily, etc.)
3. **Direct API Integration** - Custom providers for search APIs
4. **Configuration-Based Selection** - Dynamic provider switching

## Architecture Components

### 1. Base Search Provider Interface

```python
# src/konseho/tools/search_ops.py
class SearchProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Execute search and return results."""
        pass
```

### 2. Built-in Providers

- **MockSearchProvider**: General purpose testing with realistic fake results
- **Custom Fake Providers**: Domain-specific testing (news, academic, etc.)

### 3. MCP Integration

- **MCPSearchProvider**: Wraps MCP search tools to provide standardized interface
- **create_mcp_search_provider()**: Auto-detects and wraps MCP search tools
- **Response Parsing**: Handles various MCP response formats (JSON, text, lists)

### 4. Search Tool

```python
# src/konseho/tools/search_tool.py
@tool
def web_search(query: str, max_results: int = 10) -> dict:
    """Search the web using configured provider."""
    # Uses search_config.get_search_provider() or defaults to mock
```

## Usage Patterns

### Pattern 1: Direct Provider Usage

```python
from konseho.tools.search_ops import web_search, MockSearchProvider

# Use mock provider
provider = MockSearchProvider()
results = web_search("query", provider=provider)
```

### Pattern 2: MCP Tool Wrapping

```python
from konseho.tools.mcp_search_adapter import MCPSearchProvider

# Wrap MCP tool
provider = MCPSearchProvider(brave_search_tool, "brave")
results = web_search("query", provider=provider)
```

### Pattern 3: Configuration-Based

```python
import os
os.environ["SEARCH_PROVIDER"] = "fake-news"

# Provider selected based on environment
from config.search_config import get_search_provider
provider = get_search_provider()
```

### Pattern 4: Agent-Specific Providers

```python
# Different providers for different agents
news_agent = create_agent(
    name="News Researcher",
    tools=[lambda q: web_search(q, provider=NewsProvider())]
)

academic_agent = create_agent(
    name="Academic Researcher", 
    tools=[lambda q: web_search(q, provider=AcademicProvider())]
)
```

## MCP Configuration

When MCP servers are configured in `mcp.json`:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  }
}
```

The search tools become available to agents and can be wrapped with MCPSearchProvider.

## Implementation Status

### Implemented ✅
- SearchProvider abstract base class
- MockSearchProvider for testing
- web_search() function with provider parameter
- MCPSearchProvider for wrapping MCP tools
- create_mcp_search_provider() for auto-detection
- Response parsing for various formats

### Placeholder/Mock 🟡
- MCP server communication (returns mock tools)
- search_config.get_search_provider() (referenced but not implemented)

### Not Implemented ❌
- Real API providers (Brave, Tavily, Serper)
- Actual MCP protocol communication

## Best Practices

1. **Start with Mocks**: Use MockSearchProvider or fake providers during development
2. **Environment Configuration**: Use environment variables for API keys and provider selection
3. **Graceful Fallback**: Always provide fallback to mock when APIs unavailable
4. **Provider Specialization**: Give different agents different search providers based on their role
5. **Response Validation**: Ensure all providers return the standard format

## Example Files

- `examples/search_provider_demo.py` - Comprehensive demo of all patterns
- `examples/mcp_search_example.py` - MCP-specific integration examples
- `examples/real_search.py` - Template for real API integration
- `docs/search-providers.md` - Detailed documentation

## Future Enhancements

1. Implement real MCP protocol communication
2. Add more built-in providers (Wikipedia, arXiv, etc.)
3. Implement caching layer for search results
4. Add search result ranking/filtering
5. Implement search_config module for global configuration