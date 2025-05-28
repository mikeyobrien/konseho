"""Generic MCP adapter for using any MCP tools with Konseho agents."""
from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from typing import Any
from konseho.protocols import JSON


class MCPToolAdapter:
    """Adapter to make any MCP tool compatible with Konseho agents.

    This adapter handles the conversion between MCP tool responses
    (which are often strings or varied formats) and structured data
    that agents can work with effectively.
    """

    def __init__(self, mcp_tool: Callable[..., Any], name: (str | None)=None):
        """Initialize MCP tool adapter.

        Args:
            mcp_tool: The MCP tool function
            name: Optional name override (defaults to tool's __name__)
        """
        self.mcp_tool = mcp_tool
        self.name = name or getattr(mcp_tool, '__name__', 'mcp_tool')
        self.__name__ = self.name
        self.__doc__ = getattr(mcp_tool, '__doc__', '')
        self._signature = inspect.signature(mcp_tool)

    def __call__(self, *args: object, **kwargs: object) -> object:
        """Execute the MCP tool with enhanced response handling.

        Returns:
            Processed response that's more suitable for agent consumption
        """
        try:
            raw_response = self.mcp_tool(*args, **kwargs)
            processed_response = self._process_response(raw_response)
            return processed_response
        except Exception as e:
            return {'error': str(e), 'tool': self.name, 'args': {'args':
                args, 'kwargs': kwargs}}

    def _process_response(self, response: object) -> object:
        """Process MCP response to make it more structured and agent-friendly.

        Many MCP tools return strings with formatted output. This method
        attempts to extract structured data when possible.
        """
        if isinstance(response, (dict, list)):
            return response
        if isinstance(response, str):
            try:
                return json.loads(response)
            except:
                pass
            if processed := self._parse_structured_string(response):
                return processed
            return {'type': 'text', 'content': response, 'tool': self.name}
        return response

    def _parse_structured_string(self, text: str) ->(dict[str, object] | None):
        """Parse common structured string formats from MCP tools."""
        lines = text.strip().split('\n')
        if any(line.strip().startswith(('1.', '2.', '3.')) for line in lines):
            items = []
            current_item = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line[0].isdigit() and '. ' in line[:3]:
                    if current_item:
                        items.append(current_item)
                    current_item = {'text': line.split('. ', 1)[1]}
                elif current_item:
                    current_item['details'] = current_item.get('details', ''
                        ) + ' ' + line
            if current_item:
                items.append(current_item)
            if items:
                return {'type': 'list', 'items': items, 'tool': self.name}
        if any(':' in line for line in lines):
            data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip().lower().replace(' ', '_')] = value.strip()
            if data:
                return {'type': 'key_value', 'data': data, 'tool': self.name}
        return None


def adapt_mcp_tools(tools: list[object], adapt_all: bool=False) ->list[object]:
    """Adapt MCP tools for use with Konseho agents.

    Args:
        tools: List of tools (may include MCP and non-MCP tools)
        adapt_all: If True, wrap all tools. If False, only wrap likely MCP tools.

    Returns:
        List of tools with MCP tools wrapped in adapters
    """
    adapted_tools: list[object] = []
    for tool in tools:
        if should_adapt_tool(tool) or adapt_all:
            if callable(tool):
                adapted_tools.append(MCPToolAdapter(tool))
            else:
                adapted_tools.append(tool)
        else:
            adapted_tools.append(tool)
    return adapted_tools


def should_adapt_tool(tool: object) ->bool:
    """Determine if a tool should be wrapped with MCP adapter.

    Args:
        tool: Tool to check

    Returns:
        True if tool appears to be from MCP
    """
    tool_name = getattr(tool, '__name__', '').lower()
    tool_module = getattr(tool, '__module__', '').lower()
    mcp_indicators = ['mcp' in tool_module, 'mcp_' in tool_name, '_mcp' in
        tool_name, 'modelcontextprotocol' in tool_module, 'brave_search' in
        tool_name, 'tavily' in tool_name, 'firecrawl' in tool_name, 
        'github' in tool_name and 'mcp' in tool_module]
    return any(mcp_indicators)


def create_mcp_tool(name: str, description: str, mcp_function: Callable[..., Any]
    ) ->Callable[..., Any]:
    """Create a Konseho-compatible tool from an MCP function.

    This is useful when you want to manually wrap specific MCP tools
    with custom handling.

    Args:
        name: Name for the tool
        description: Description of what the tool does
        mcp_function: The MCP function to wrap

    Returns:
        Wrapped tool function compatible with Konseho

    Example:
        github_tool = create_mcp_tool(
            "github_search",
            "Search GitHub repositories",
            mcp_github.search_repos
        )
    """
    adapter = MCPToolAdapter(mcp_function, name)
    adapter.__doc__ = description
    sig = inspect.signature(mcp_function)
    # Store signature for inspection
    setattr(adapter, '__signature__', sig)
    return adapter


"""
# Example 1: Adapt all MCP tools automatically
from konseho.tools.mcp_adapter import adapt_mcp_tools

# If you have MCP tools mixed with regular tools
adapted_tools = adapt_mcp_tools(agent.tools)
agent.tools = adapted_tools

# Example 2: Manually wrap specific MCP tools
from konseho.tools.mcp_adapter import MCPToolAdapter

# Wrap a specific MCP tool
wrapped_github = MCPToolAdapter(github_mcp_tool)
agent.tools.append(wrapped_github)

# Example 3: Create custom MCP tool
from konseho.tools.mcp_adapter import create_mcp_tool

search_tool = create_mcp_tool(
    "search_repos",
    "Search GitHub repositories for code",
    github_mcp.search_repositories
)
"""
