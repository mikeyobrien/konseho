"""Search provider configuration for Konseho."""
from __future__ import annotations

import os
from konseho.mcp.config import MCPConfigManager
from konseho.tools.mcp_search_adapter import MCPSearchProvider
from konseho.tools.search_ops import MockSearchProvider, SearchProvider
_search_provider: SearchProvider | None = None


def get_search_provider() ->SearchProvider:
    """Get the configured search provider.

    Priority:
    1. If a provider is explicitly set, use it
    2. If SEARCH_PROVIDER env var is set to an MCP server name, use that
    3. If SEARCH_PROVIDER env var is set to another value, try to create appropriate provider
    4. Default to MockSearchProvider

    Returns:
        SearchProvider instance
    """
    global _search_provider
    if _search_provider is not None:
        return _search_provider
    provider_name = os.environ.get('SEARCH_PROVIDER', '').lower()
    if not provider_name:
        if provider := _try_mcp_auto_detect():
            return provider
        return MockSearchProvider()
    if provider_name in ['brave-search', 'brave_search', 'tavily', 'serper']:
        if provider := _create_mcp_provider(provider_name):
            return provider
    if provider_name == 'mock':
        return MockSearchProvider()
    if provider := _create_mcp_provider(provider_name):
        return provider
    print(
        f"Warning: Unknown search provider '{provider_name}', using mock provider"
        )
    return MockSearchProvider()


def set_search_provider(provider: SearchProvider):
    """Set the global search provider.

    Args:
        provider: SearchProvider instance to use globally
    """
    global _search_provider
    _search_provider = provider


def _try_mcp_auto_detect() ->(SearchProvider | None):
    """Try to auto-detect search provider from MCP configuration.

    Returns:
        SearchProvider if found, None otherwise
    """
    try:
        config_manager = MCPConfigManager()
        servers = config_manager.list_servers()
        search_servers = ['brave-search', 'tavily', 'serper', 'web-search']
        for server_name in servers:
            if any(search in server_name.lower() for search in search_servers):
                if provider := _create_mcp_provider(server_name):
                    print(f'Auto-detected search provider: {server_name}')
                    return provider
    except Exception:
        pass
    return None


def _create_mcp_provider(server_name: str) ->(SearchProvider | None):
    """Create an MCP-based search provider.

    Args:
        server_name: Name of the MCP server

    Returns:
        MCPSearchProvider if successful, None otherwise
    """
    try:
        try:
            from konseho.mcp.strands_integration import StrandsMCPManager
            manager = StrandsMCPManager()
            tools = manager.get_tools(server_name)
            for tool in tools:
                if hasattr(tool, 'tool_name'
                    ) and 'search' in tool.tool_name.lower():
                    print(
                        f'Using real MCP search tool from {server_name}: {tool.tool_name}'
                        )
                    return MCPSearchProvider(tool, server_name)
                elif hasattr(tool, '__name__'
                    ) and 'search' in tool.__name__.lower():
                    print(f'Using real MCP search tool from {server_name}')
                    return MCPSearchProvider(tool, server_name)
        except Exception as e:
            print(f'Could not connect to real MCP server {server_name}: {e}')
            print('Falling back to mock provider')
        if 'brave' in server_name.lower():

            def mock_brave_search(query: str, count: int=10) ->str:
                """Mock Brave Search MCP tool for demonstration."""
                return f"""Web search results for "{query}" from Brave Search:

1. {query.title()} - Official Documentation
   https://docs.example.com/{query.replace(' ', '-').lower()}
   The official documentation and guides for {query}.

2. Understanding {query.title()} - Developer Guide  
   https://dev.example.com/guides/{query.replace(' ', '-').lower()}
   A comprehensive developer guide to {query} with examples.

3. {query.title()} Best Practices 2024
   https://bestpractices.example.com/{query.replace(' ', '-').lower()}
   Industry standards and recommendations for {query}.

Note: Using mock Brave Search (real MCP server not available)."""
            return MCPSearchProvider(mock_brave_search, 'brave-search')
        elif 'tavily' in server_name.lower():

            def mock_tavily_search(query: str, max_results: int=10) ->str:
                import json
                results = [{'title': f'{query.title()} Overview', 'url':
                    f"https://tavily.example.com/{query.replace(' ', '-')}",
                    'snippet':
                    f'Comprehensive overview of {query} from Tavily search.'
                    }, {'title': f'Latest {query.title()} Research', 'url':
                    f"https://research.tavily.com/{query.replace(' ', '-')}",
                    'snippet': f'Recent research and developments in {query}.'}
                    ]
                return json.dumps(results)
            return MCPSearchProvider(mock_tavily_search, 'tavily')

        def generic_mcp_search(query: str, **kwargs) ->str:
            return f"Search results for '{query}' from {server_name}"
        return MCPSearchProvider(generic_mcp_search, server_name)
    except Exception as e:
        print(f'Failed to create MCP provider for {server_name}: {e}')
        return None


def get_provider_by_name(name: str) ->(SearchProvider | None):
    """Get a search provider by name.

    Args:
        name: Provider name (mock, brave-search, tavily, etc.)

    Returns:
        SearchProvider if found, None otherwise
    """
    name = name.lower()
    if name == 'mock':
        return MockSearchProvider()
    return _create_mcp_provider(name)
