"""MCP Search Provider adapter for using MCP search tools with Konseho's search system."""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import cast, Protocol
from konseho.protocols import JSON
from .search_ops import SearchProvider


class MCPTool(Protocol):
    """Protocol for MCP tool functions."""
    def __call__(self, **kwargs: object) -> object: ...
    def invoke(self, **kwargs: object) -> object: ...


class MCPSearchProvider(SearchProvider):
    """Adapter to use MCP search tools as search providers.

    This provider wraps MCP search tools (like brave_search, tavily_search, etc.)
    and adapts their responses to the standard search result format.
    """

    def __init__(self, mcp_tool: MCPTool, provider_name: (str | None)=None):
        """Initialize MCP search provider.

        Args:
            mcp_tool: The MCP search tool function
            provider_name: Optional name override (defaults to extracting from tool name)
        """
        self.mcp_tool = mcp_tool
        self._provider_name = provider_name or self._extract_provider_name(
            mcp_tool)

    @property
    def name(self) ->str:
        """Return the provider name."""
        return self._provider_name

    def _extract_provider_name(self, tool: MCPTool) ->str:
        """Extract provider name from tool function."""
        if hasattr(tool, 'tool_name'):
            tool_name = str(getattr(tool, 'tool_name')).lower()
        else:
            tool_name = getattr(tool, '__name__', 'mcp_search').lower()
        if 'brave' in tool_name:
            return 'brave'
        elif 'tavily' in tool_name:
            return 'tavily'
        elif 'serper' in tool_name:
            return 'serper'
        elif 'google' in tool_name:
            return 'google'
        elif 'bing' in tool_name:
            return 'bing'
        else:
            parts = tool_name.split('__')
            if len(parts) >= 2:
                return str(parts[1])
            return 'mcp'

    def search(self, query: str, max_results: int=10) ->list[dict[str, str]]:
        """Execute search using the MCP tool.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, and snippet
        """
        try:
            if hasattr(self.mcp_tool, 'invoke'):
                response = self.mcp_tool.invoke(query=query, count=max_results)
            else:
                try:
                    response = self.mcp_tool(query=query, count=max_results)
                except TypeError:
                    try:
                        response = self.mcp_tool(query=query, max_results=
                            max_results)
                    except TypeError:
                        response = self.mcp_tool(query=query)
            return self._parse_response(response, max_results)
        except Exception as e:
            print(f'MCP search error: {e}')
            return []

    def _parse_response(self, response: object, max_results: int) ->list[dict[
        str, str]]:
        """Parse MCP tool response into standard search results format."""
        results = []
        if isinstance(response, list) and all(isinstance(r, dict) for r in
            response):
            for item in response[:max_results]:
                result = {'title': str(item.get('title', item.get('name',
                    'Untitled'))), 'url': str(item.get('url', item.get(
                    'link', item.get('href', '#')))), 'snippet': str(item.
                    get('snippet', item.get('description', item.get(
                    'content', 'No description available'))))}
                results.append(result)
            return results
        if isinstance(response, dict):
            if 'results' in response:
                return self._parse_response(response['results'], max_results)
            elif 'items' in response:
                return self._parse_response(response['items'], max_results)
            elif 'data' in response:
                return self._parse_response(response['data'], max_results)
            elif any(key in response for key in ['title', 'url', 'link']):
                return self._parse_response([response], max_results)
        if isinstance(response, str):
            try:
                json_data = json.loads(response)
                return self._parse_response(json_data, max_results)
            except:
                pass
            if results := self._parse_text_response(response, max_results):
                return results
        return [{'title': 'Search Result', 'url': '#', 'snippet': str(
            response)[:500]}]

    def _parse_text_response(self, text: str, max_results: int) ->list[dict
        [str, str]]:
        """Parse text-based search responses."""
        results = []
        lines = text.strip().split('\n')
        current_result = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if num_match := re.match('^(\\d+)\\.\\s+(.+)', line):
                if current_result and current_result.get('title'):
                    results.append(current_result)
                content = num_match.group(2)
                current_result = {'title': '', 'url': '#', 'snippet': ''}
                if url_match := re.search('https?://[^\\s]+', content):
                    current_result['url'] = url_match.group(0)
                    if title_part := content[:url_match.start()].strip(' -'):
                        current_result['title'] = title_part
                    else:
                        current_result['title'] = content[url_match.end():
                            ].strip(' -') or 'Search Result'
                else:
                    current_result['title'] = content
            elif re.match('^https?://', line):
                if current_result:
                    current_result['url'] = line
            elif current_result and not line[0].isdigit():
                if current_result['snippet']:
                    current_result['snippet'] += ' ' + line
                else:
                    current_result['snippet'] = line
        if current_result and current_result.get('title'):
            results.append(current_result)
        if not results:
            for i, line in enumerate(lines[:max_results]):
                line = line.strip()
                if line and not line.startswith('#'):
                    if line := re.sub('^[-*•]\\s*', '', line):
                        results.append({'title': line[:100] + ('...' if len
                            (line) > 100 else ''), 'url': '#', 'snippet': line}
                            )
        return results[:max_results]


def create_mcp_search_provider(tool_pattern: str, tools: list[object]) ->(
    MCPSearchProvider | None):
    """Create an MCP search provider from available tools.

    Args:
        tool_pattern: Pattern to match tool names (e.g., 'brave', 'search', 'tavily')
        tools: List of available tools

    Returns:
        MCPSearchProvider instance or None if no matching tool found

    Example:
        >>> tools = [mcp__brave__search, mcp__tavily__search, some_other_tool]
        >>> provider = create_mcp_search_provider('brave', tools)
        >>> if provider:
        ...     results = provider.search("python tutorials")
    """
    pattern_lower = tool_pattern.lower()
    for tool in tools:
        tool_name = getattr(tool, '__name__', '').lower()
        if pattern_lower in tool_name:
            search_indicators = ['search', 'find', 'query', 'lookup']
            if any(indicator in tool_name for indicator in search_indicators):
                if callable(tool):
                    return MCPSearchProvider(cast(MCPTool, tool))
    for tool in tools:
        tool_name = getattr(tool, '__name__', '').lower()
        tool_doc = (getattr(tool, '__doc__', '') or '').lower()
        if ('search' in tool_name or 'search' in tool_doc
            ) and pattern_lower in tool_name:
            if callable(tool):
                return MCPSearchProvider(cast(MCPTool, tool))
    return None


def find_mcp_search_provider(tools: list[object]) ->(MCPSearchProvider | None):
    """Find any available MCP search provider from tools.

    Args:
        tools: List of available tools

    Returns:
        First available MCPSearchProvider or None

    Example:
        >>> provider = find_mcp_search_provider(agent.tools)
        >>> if provider:
        ...     results = provider.search("machine learning")
    """
    search_patterns = ['brave', 'tavily', 'serper', 'google', 'bing', 'search']
    for pattern in search_patterns:
        if provider := create_mcp_search_provider(pattern, tools):
            return provider
    return None
