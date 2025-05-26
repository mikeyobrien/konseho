# Configuring Search Providers

The Konseho search tool supports pluggable search providers, allowing you to use your preferred search service.

## Default Provider

By default, the search tool uses a mock provider that generates realistic-looking results for testing and demonstration purposes. This requires no configuration and works out of the box.

## Using MCP Search Servers

If you have MCP (Model Context Protocol) servers configured with search capabilities, you can use them directly with Konseho's search tool.

### Quick Setup with MCP

```python
from konseho.tools.search_ops import web_search
from konseho.tools.mcp_search_adapter import MCPSearchProvider

# Assuming you have brave_search from MCP available in your agent's tools
# (e.g., after running: claude mcp add brave-search npx @modelcontextprotocol/server-brave-search)

# Create provider from MCP tool
provider = MCPSearchProvider(brave_search, "brave-mcp")

# Use it for searches
results = web_search("python tutorials", provider=provider)
```

### Automatic MCP Tool Detection

```python
from konseho.tools.mcp_search_adapter import create_mcp_search_provider

# Automatically find and wrap MCP search tool
provider = create_mcp_search_provider("brave_search", agent.tools)
if provider:
    results = web_search("konseho multi-agent", provider=provider)
else:
    # Fallback to default
    results = web_search("konseho multi-agent")
```

### Configuring MCP Search Servers

First, add an MCP search server using Claude CLI:

```bash
# Add Brave Search MCP server
claude mcp add brave-search npx @modelcontextprotocol/server-brave-search

# Add other search servers
claude mcp add tavily npx @tavily/mcp-server
```

Then use in your agents:

```python
from konseho.agents.base import create_agent
from konseho.tools.mcp_search_adapter import create_mcp_search_provider

# Create agent with MCP tools
agent = create_agent(
    name="Researcher",
    tools=[brave_search, file_write, ...]  # MCP tools included
)

# Create search provider from MCP tool
search_provider = create_mcp_search_provider("brave_search", agent.tools)

# Now the agent can use web_search with MCP backend
def search_with_mcp(query: str, max_results: int = 10):
    return web_search(query, max_results=max_results, provider=search_provider)
```

## Implementing Custom Providers

To use a real search service, implement a custom provider by extending the `SearchProvider` base class:

```python
from konseho.tools.search_ops import SearchProvider
from typing import List, Dict

class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize your client here
        from tavily import TavilyClient
        self.client = TavilyClient(api_key=api_key)
    
    @property
    def name(self) -> str:
        return "tavily"
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        # Call the Tavily API
        response = self.client.search(query, max_results=max_results)
        
        # Transform results to our format
        return [
            {
                "title": result["title"],
                "url": result["url"],
                "snippet": result["content"][:200] + "..."
            }
            for result in response["results"]
        ]
```

## Example Providers

### Brave Search Provider

```python
class BraveSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
    
    @property
    def name(self) -> str:
        return "brave"
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        import requests
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": max_results
        }
        
        response = requests.get(self.base_url, headers=headers, params=params)
        data = response.json()
        
        return [
            {
                "title": result["title"],
                "url": result["url"],
                "snippet": result.get("description", "")[:200]
            }
            for result in data.get("web", {}).get("results", [])
        ]
```

### SerpAPI Provider

```python
class SerpAPIProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        from serpapi import GoogleSearch
        self.client = GoogleSearch
    
    @property
    def name(self) -> str:
        return "serpapi"
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": max_results
        }
        
        search = self.client(params)
        results = search.get_dict().get("organic_results", [])
        
        return [
            {
                "title": result["title"],
                "url": result["link"],
                "snippet": result.get("snippet", "")
            }
            for result in results[:max_results]
        ]
```

## Using Custom Providers

### Option 1: Direct Usage

```python
from konseho.tools.search_ops import web_search

# Initialize your provider
provider = TavilySearchProvider(api_key="your-api-key")

# Use it in searches
results = web_search("python tutorials", provider=provider)
```

### Option 2: In Agent Configuration

```python
from konseho.agents.base import create_agent
from konseho.tools.search_ops import web_search

# Create provider
search_provider = BraveSearchProvider(api_key="your-api-key")

# Create search tool with bound provider
def configured_search(query: str, max_results: int = 10):
    return web_search(query, max_results=max_results, provider=search_provider)

# Add to agent tools
agent = create_agent(
    name="Researcher",
    tools=[configured_search, file_write, ...],
    system_prompt="You are a research assistant..."
)
```

### Option 3: Global Configuration

Create a configuration module:

```python
# config/search_config.py
import os
from konseho.tools.search_ops import SearchProvider

def get_search_provider() -> SearchProvider:
    provider_name = os.environ.get("SEARCH_PROVIDER", "mock").lower()
    
    if provider_name == "tavily":
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable required")
        return TavilySearchProvider(api_key)
    
    elif provider_name == "brave":
        api_key = os.environ.get("BRAVE_API_KEY")
        if not api_key:
            raise ValueError("BRAVE_API_KEY environment variable required")
        return BraveSearchProvider(api_key)
    
    else:
        from konseho.tools.search_ops import MockSearchProvider
        return MockSearchProvider()
```

Then use it in your agents:

```python
from config.search_config import get_search_provider
from konseho.tools.search_ops import web_search

provider = get_search_provider()
results = web_search("query", provider=provider)
```

## API Key Security

**Important**: Never hardcode API keys in your source code. Use environment variables or secure configuration files:

```bash
# .env file (add to .gitignore)
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your-api-key-here

# Or export in shell
export SEARCH_PROVIDER=brave
export BRAVE_API_KEY=your-api-key-here
```

## Testing Your Provider

Always test your provider implementation:

```python
def test_my_provider():
    provider = MySearchProvider(api_key="test-key")
    
    # Test basic search
    results = provider.search("test query", max_results=5)
    assert len(results) <= 5
    
    # Test result format
    for result in results:
        assert "title" in result
        assert "url" in result
        assert "snippet" in result
        assert isinstance(result["title"], str)
        assert result["url"].startswith("http")
```

## Provider Requirements

All search providers must:

1. Extend the `SearchProvider` base class
2. Implement the `name` property (return a string identifier)
3. Implement the `search(query, max_results)` method
4. Return results in the standard format:
   ```python
   [
       {
           "title": "Result Title",
           "url": "https://example.com/page",
           "snippet": "Brief description of the result..."
       },
       ...
   ]
   ```
5. Handle errors gracefully (raise exceptions for the tool to catch)

## Supported Providers

While Konseho provides the framework for any search provider, here are some popular options:

- **Tavily**: AI-focused search API (https://tavily.com)
- **Brave Search**: Privacy-focused search API (https://brave.com/search/api/)
- **SerpAPI**: Google search results API (https://serpapi.com)
- **Bing Search**: Microsoft's search API
- **DuckDuckGo**: Via their instant answer API
- **Custom**: Any API that returns search results

Choose based on your needs for accuracy, cost, rate limits, and privacy requirements.