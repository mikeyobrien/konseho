"""MCP Search Provider adapter for using MCP search tools with Konseho's search system."""

import json
import re
from collections.abc import Callable
from typing import Any

from .search_ops import SearchProvider


class MCPSearchProvider(SearchProvider):
    """Adapter to use MCP search tools as search providers.

    This provider wraps MCP search tools (like brave_search, tavily_search, etc.)
    and adapts their responses to the standard search result format.
    """

    def __init__(self, mcp_tool: Callable, provider_name: str | None = None):
        """Initialize MCP search provider.

        Args:
            mcp_tool: The MCP search tool function
            provider_name: Optional name override (defaults to extracting from tool name)
        """
        self.mcp_tool = mcp_tool
        self._provider_name = provider_name or self._extract_provider_name(mcp_tool)

    @property
    def name(self) -> str:
        """Return the provider name."""
        return self._provider_name

    def _extract_provider_name(self, tool: Callable) -> str:
        """Extract provider name from tool function."""
        # Check for MCPAgentTool with tool_name
        if hasattr(tool, "tool_name"):
            tool_name = tool.tool_name.lower()
        else:
            tool_name = getattr(tool, "__name__", "mcp_search").lower()

        # Extract provider from common patterns
        if "brave" in tool_name:
            return "brave"
        elif "tavily" in tool_name:
            return "tavily"
        elif "serper" in tool_name:
            return "serper"
        elif "google" in tool_name:
            return "google"
        elif "bing" in tool_name:
            return "bing"
        else:
            # Try to extract from format like "mcp__provider__search"
            parts = tool_name.split("__")
            if len(parts) >= 2:
                return parts[1]
            return "mcp"

    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        """Execute search using the MCP tool.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, and snippet
        """
        try:
            # Call the MCP tool
            # Check if it's an MCPAgentTool with invoke method
            if hasattr(self.mcp_tool, "invoke"):
                # MCPAgentTool - use invoke method
                response = self.mcp_tool.invoke(query=query, count=max_results)
            else:
                # Regular callable tool
                try:
                    # Try with count parameter (common for Brave search)
                    response = self.mcp_tool(query=query, count=max_results)
                except TypeError:
                    try:
                        # Try with max_results parameter
                        response = self.mcp_tool(query=query, max_results=max_results)
                    except TypeError:
                        # Fall back to just query
                        response = self.mcp_tool(query=query)

            # Parse the response based on its type
            return self._parse_response(response, max_results)

        except Exception as e:
            # Return empty results on error
            print(f"MCP search error: {e}")
            return []

    def _parse_response(self, response: Any, max_results: int) -> list[dict[str, str]]:
        """Parse MCP tool response into standard search results format."""
        results = []

        # If response is already a list of dicts with the right format
        if isinstance(response, list) and all(isinstance(r, dict) for r in response):
            for item in response[:max_results]:
                result = {
                    "title": str(item.get("title", item.get("name", "Untitled"))),
                    "url": str(
                        item.get("url", item.get("link", item.get("href", "#")))
                    ),
                    "snippet": str(
                        item.get(
                            "snippet",
                            item.get(
                                "description",
                                item.get("content", "No description available"),
                            ),
                        )
                    ),
                }
                results.append(result)
            return results

        # If response is a dict with results key
        if isinstance(response, dict):
            if "results" in response:
                return self._parse_response(response["results"], max_results)
            elif "items" in response:
                return self._parse_response(response["items"], max_results)
            elif "data" in response:
                return self._parse_response(response["data"], max_results)
            # Single result as dict
            elif any(key in response for key in ["title", "url", "link"]):
                return self._parse_response([response], max_results)

        # If response is a string, try to parse it
        if isinstance(response, str):
            # Try JSON parsing first
            try:
                json_data = json.loads(response)
                return self._parse_response(json_data, max_results)
            except:
                pass

            # Parse structured text formats
            results = self._parse_text_response(response, max_results)
            if results:
                return results

        # Fallback: wrap the response as a single result
        return [{"title": "Search Result", "url": "#", "snippet": str(response)[:500]}]

    def _parse_text_response(self, text: str, max_results: int) -> list[dict[str, str]]:
        """Parse text-based search responses."""
        results = []
        lines = text.strip().split("\n")

        # Pattern 1: Numbered results with title, URL, and description
        # Example: "1. Title Here - https://example.com\n   Description here..."
        current_result = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for numbered item (e.g., "1. ", "2. ")
            num_match = re.match(r"^(\d+)\.\s+(.+)", line)
            if num_match:
                # Save previous result if exists
                if current_result and current_result.get("title"):
                    results.append(current_result)

                # Start new result
                content = num_match.group(2)
                current_result = {"title": "", "url": "#", "snippet": ""}

                # Try to extract URL from the line
                url_match = re.search(r"https?://[^\s]+", content)
                if url_match:
                    current_result["url"] = url_match.group(0)
                    # Title is everything before the URL
                    title_part = content[: url_match.start()].strip(" -")
                    if title_part:
                        current_result["title"] = title_part
                    else:
                        # Or after the URL
                        current_result["title"] = (
                            content[url_match.end() :].strip(" -") or "Search Result"
                        )
                else:
                    current_result["title"] = content

            # Pattern 2: URL on its own line
            elif re.match(r"^https?://", line):
                if current_result:
                    current_result["url"] = line

            # Pattern 3: Description/snippet lines (usually indented or following a result)
            elif current_result and not line[0].isdigit():
                if current_result["snippet"]:
                    current_result["snippet"] += " " + line
                else:
                    current_result["snippet"] = line

        # Don't forget the last result
        if current_result and current_result.get("title"):
            results.append(current_result)

        # Pattern 4: Simple bullet points or lines
        if not results:
            for i, line in enumerate(lines[:max_results]):
                line = line.strip()
                if line and not line.startswith("#"):  # Skip headers
                    # Remove common prefixes
                    line = re.sub(r"^[-*•]\s*", "", line)
                    if line:
                        results.append(
                            {
                                "title": line[:100]
                                + ("..." if len(line) > 100 else ""),
                                "url": "#",
                                "snippet": line,
                            }
                        )

        return results[:max_results]


def create_mcp_search_provider(
    tool_pattern: str, tools: list[Any]
) -> MCPSearchProvider | None:
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

    # Find matching MCP search tools
    for tool in tools:
        tool_name = getattr(tool, "__name__", "").lower()

        # Check if tool name matches pattern
        if pattern_lower in tool_name:
            # Additional check for search-related tools
            search_indicators = ["search", "find", "query", "lookup"]
            if any(indicator in tool_name for indicator in search_indicators):
                return MCPSearchProvider(tool)

    # Try more flexible matching
    for tool in tools:
        tool_name = getattr(tool, "__name__", "").lower()
        tool_doc = (getattr(tool, "__doc__", "") or "").lower()

        # Check if it's a search tool based on name or docs
        if (
            "search" in tool_name or "search" in tool_doc
        ) and pattern_lower in tool_name:
            return MCPSearchProvider(tool)

    return None


# Convenience function for finding any MCP search provider
def find_mcp_search_provider(tools: list[Any]) -> MCPSearchProvider | None:
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
    # Try common search providers in order of preference
    search_patterns = ["brave", "tavily", "serper", "google", "bing", "search"]

    for pattern in search_patterns:
        provider = create_mcp_search_provider(pattern, tools)
        if provider:
            return provider

    return None
