"""Generic MCP adapter for using any MCP tools with Konseho agents."""

from typing import Any, Callable, List, Optional, Dict
import inspect
import json


class MCPToolAdapter:
    """Adapter to make any MCP tool compatible with Konseho agents.
    
    This adapter handles the conversion between MCP tool responses
    (which are often strings or varied formats) and structured data
    that agents can work with effectively.
    """
    
    def __init__(self, mcp_tool: Callable, name: Optional[str] = None):
        """Initialize MCP tool adapter.
        
        Args:
            mcp_tool: The MCP tool function
            name: Optional name override (defaults to tool's __name__)
        """
        self.mcp_tool = mcp_tool
        self.name = name or getattr(mcp_tool, '__name__', 'mcp_tool')
        
        # Preserve original function metadata
        self.__name__ = self.name
        self.__doc__ = getattr(mcp_tool, '__doc__', '')
        
        # Get tool signature for parameter handling
        self._signature = inspect.signature(mcp_tool)
    
    def __call__(self, *args, **kwargs) -> Any:
        """Execute the MCP tool with enhanced response handling.
        
        Returns:
            Processed response that's more suitable for agent consumption
        """
        try:
            # Call the MCP tool
            raw_response = self.mcp_tool(*args, **kwargs)
            
            # Process the response to make it more agent-friendly
            processed_response = self._process_response(raw_response)
            
            return processed_response
            
        except Exception as e:
            # Return error in a structured format
            return {
                "error": str(e),
                "tool": self.name,
                "args": {"args": args, "kwargs": kwargs}
            }
    
    def _process_response(self, response: Any) -> Any:
        """Process MCP response to make it more structured and agent-friendly.
        
        Many MCP tools return strings with formatted output. This method
        attempts to extract structured data when possible.
        """
        # If already structured, return as-is
        if isinstance(response, (dict, list)):
            return response
        
        # If string, try to extract structure
        if isinstance(response, str):
            # Try to parse as JSON first
            try:
                return json.loads(response)
            except:
                pass
            
            # Check for common structured string patterns
            processed = self._parse_structured_string(response)
            if processed:
                return processed
            
            # Return wrapped string for better handling
            return {
                "type": "text",
                "content": response,
                "tool": self.name
            }
        
        # For other types, return as-is
        return response
    
    def _parse_structured_string(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse common structured string formats from MCP tools."""
        lines = text.strip().split('\n')
        
        # Check for numbered list format
        if any(line.strip().startswith(('1.', '2.', '3.')) for line in lines):
            items = []
            current_item = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for numbered item
                if line[0].isdigit() and '. ' in line[:3]:
                    if current_item:
                        items.append(current_item)
                    current_item = {"text": line.split('. ', 1)[1]}
                elif current_item:
                    # Additional info for current item
                    current_item["details"] = current_item.get("details", "") + " " + line
            
            if current_item:
                items.append(current_item)
            
            if items:
                return {
                    "type": "list",
                    "items": items,
                    "tool": self.name
                }
        
        # Check for key-value format
        if any(':' in line for line in lines):
            data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip().lower().replace(' ', '_')] = value.strip()
            
            if data:
                return {
                    "type": "key_value",
                    "data": data,
                    "tool": self.name
                }
        
        return None


def adapt_mcp_tools(tools: List[Any], adapt_all: bool = False) -> List[Any]:
    """Adapt MCP tools for use with Konseho agents.
    
    Args:
        tools: List of tools (may include MCP and non-MCP tools)
        adapt_all: If True, wrap all tools. If False, only wrap likely MCP tools.
        
    Returns:
        List of tools with MCP tools wrapped in adapters
    """
    adapted_tools = []
    
    for tool in tools:
        # Check if it's likely an MCP tool
        if should_adapt_tool(tool) or adapt_all:
            adapted_tools.append(MCPToolAdapter(tool))
        else:
            adapted_tools.append(tool)
    
    return adapted_tools


def should_adapt_tool(tool: Any) -> bool:
    """Determine if a tool should be wrapped with MCP adapter.
    
    Args:
        tool: Tool to check
        
    Returns:
        True if tool appears to be from MCP
    """
    # Check for MCP indicators
    tool_name = getattr(tool, '__name__', '').lower()
    tool_module = getattr(tool, '__module__', '').lower()
    
    # Common MCP indicators
    mcp_indicators = [
        'mcp' in tool_module,
        'mcp_' in tool_name,
        '_mcp' in tool_name,
        'modelcontextprotocol' in tool_module,
        # Common MCP server tools
        'brave_search' in tool_name,
        'tavily' in tool_name,
        'firecrawl' in tool_name,
        'github' in tool_name and 'mcp' in tool_module,
    ]
    
    return any(mcp_indicators)


def create_mcp_tool(name: str, description: str, mcp_function: Callable) -> Callable:
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
    
    # Preserve parameter information
    sig = inspect.signature(mcp_function)
    adapter.__signature__ = sig
    
    return adapter


# Example usage documentation
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