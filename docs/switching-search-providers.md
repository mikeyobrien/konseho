# Switching Search Providers in Konseho

This guide explains how to configure and switch between different search providers in Konseho.

## Overview

Konseho supports multiple search providers through a flexible plugin architecture:

1. **Mock Provider** - Built-in testing provider (no API key required)
2. **MCP Servers** - Use search servers configured in `mcp.json`
3. **Custom Providers** - Implement your own search provider

## Quick Start: Using MCP Search Servers

### Step 1: Configure MCP Server

Add your search server to `mcp.json`:

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

### Step 2: Set Environment Variables

```bash
# Set your API key
export BRAVE_API_KEY="your-api-key-here"

# Tell Konseho to use brave-search
export SEARCH_PROVIDER="brave-search"
```

### Step 3: Use in Your Agents

```python
from konseho.agents.base import create_agent
from konseho.tools.search_tool import web_search

agent = create_agent(
    name="Researcher",
    tools=[web_search]  # Will automatically use brave-search
)

# The agent will now use Brave Search for web queries
agent("Find the latest news about AI")
```

## Switching Between Providers

### Method 1: Environment Variable (Recommended)

Set the `SEARCH_PROVIDER` environment variable:

```bash
# Use Brave Search
export SEARCH_PROVIDER="brave-search"

# Use Tavily
export SEARCH_PROVIDER="tavily"

# Use mock provider (default)
export SEARCH_PROVIDER="mock"

# Or unset to use auto-detection
unset SEARCH_PROVIDER
```

### Method 2: Programmatic Configuration

```python
from konseho.tools.search_config import set_search_provider, get_provider_by_name

# Switch to a specific provider
provider = get_provider_by_name("brave-search")
set_search_provider(provider)

# Now all agents will use Brave Search
```

### Method 3: Per-Agent Configuration

```python
from konseho.tools.search_ops import web_search
from konseho.tools.search_config import get_provider_by_name

# Create provider-specific search functions
brave_search = lambda q: web_search(q, provider=get_provider_by_name("brave-search"))
tavily_search = lambda q: web_search(q, provider=get_provider_by_name("tavily"))

# Give different agents different search providers
news_agent = create_agent(
    name="News Agent",
    tools=[brave_search]
)

research_agent = create_agent(
    name="Research Agent", 
    tools=[tavily_search]
)
```

## Supported MCP Search Servers

### Brave Search

```json
{
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "${BRAVE_API_KEY}"
    }
  }
}
```

Get API key from: https://brave.com/search/api/

### Tavily Search

```json
{
  "tavily": {
    "command": "npx",
    "args": ["-y", "@tavily/mcp-server"],
    "env": {
      "TAVILY_API_KEY": "${TAVILY_API_KEY}"
    }
  }
}
```

Get API key from: https://tavily.com

### Perplexity Search

```json
{
  "perplexity": {
    "command": "npx",
    "args": ["-y", "@perplexity/mcp-server"],
    "env": {
      "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
    }
  }
}
```

## Implementing Custom Search Providers

If your preferred search service doesn't have an MCP server, you can implement a custom provider:

```python
from konseho.tools.search_ops import SearchProvider
from typing import List, Dict
import requests

class SerperSearchProvider(SearchProvider):
    """Google Search via Serper.dev API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    @property
    def name(self) -> str:
        return "serper"
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Execute search using Serper API."""
        response = requests.post(
            'https://google.serper.dev/search',
            headers={'X-API-KEY': self.api_key},
            json={'q': query, 'num': max_results}
        )
        
        data = response.json()
        results = []
        
        for item in data.get('organic', [])[:max_results]:
            results.append({
                'title': item['title'],
                'url': item['link'],
                'snippet': item.get('snippet', '')
            })
            
        return results

# Use the custom provider
from konseho.tools.search_config import set_search_provider

provider = SerperSearchProvider(api_key="your-serper-api-key")
set_search_provider(provider)
```

## Auto-Detection

If no provider is explicitly configured, Konseho will:

1. Check for `SEARCH_PROVIDER` environment variable
2. Look for search servers in `mcp.json` (brave-search, tavily, etc.)
3. Fall back to mock provider

## Troubleshooting

### "Using mock provider" message

This means Konseho couldn't connect to the MCP server. Check:

1. MCP server is properly configured in `mcp.json`
2. Required npm packages are installed
3. API keys are set in environment
4. You have the `mcp` Python package installed

### MCP Connection Issues

Enable debug logging:

```python
import logging
logging.getLogger("konseho.mcp").setLevel(logging.DEBUG)
```

### Provider Not Found

Ensure the provider name matches exactly:
- `brave-search` (not `brave` or `brave_search`)
- `tavily` (not `tavily-search`)

## Best Practices

1. **Development**: Use mock provider to avoid API costs
2. **Testing**: Create custom fake providers for specific test scenarios
3. **Production**: Use MCP servers for reliability and standardization
4. **API Keys**: Always use environment variables, never hardcode

## Example: Complete Setup

```python
import os
from konseho.agents.base import create_agent
from konseho.tools.search_tool import web_search
from konseho.core.council import Council
from konseho.core.steps import ParallelStep

# Configure search provider via environment
os.environ["SEARCH_PROVIDER"] = "brave-search"
os.environ["BRAVE_API_KEY"] = "your-key-here"

# Create agents that will use Brave Search
researcher = create_agent(
    name="Researcher",
    system_prompt="You find information using web search.",
    tools=[web_search]
)

fact_checker = create_agent(
    name="Fact Checker",
    system_prompt="You verify facts using web search.",
    tools=[web_search]
)

# Both agents will use the same search provider
council = Council(
    name="Research Team",
    steps=[
        ParallelStep(
            agents=[researcher, fact_checker]
        )
    ]
)

# Execute research - both agents use Brave Search
result = await council.execute("Latest AI developments")
```