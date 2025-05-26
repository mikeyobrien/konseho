"""Search tool properly decorated for Strands agents."""

from strands import tool
from typing import Dict, Any, List
from .search_ops import web_search as web_search_func
from .search_config import get_search_provider


@tool
def web_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search the web for information.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        Dictionary containing search results with query, provider, and results list
        
    Example:
        web_search("latest AI news")
    """
    # Use the configured search provider if available
    provider = get_search_provider()
    return web_search_func(query, max_results, provider=provider)