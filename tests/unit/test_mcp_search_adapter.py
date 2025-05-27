"""Tests for MCP search adapter."""


import pytest

from konseho.tools.mcp_search_adapter import (
    MCPSearchProvider,
    create_mcp_search_provider,
)


class TestMCPSearchProvider:
    """Test the MCPSearchProvider adapter."""
    
    def test_mcp_provider_with_string_response(self):
        """Test MCP provider with string response format."""
        # Mock MCP tool that returns string
        def mock_brave_search(query, count=10):
            return """
1. Python Tutorial - Official Documentation - https://docs.python.org
   The official Python tutorial covering all basics.
   
2. Learn Python - Interactive Tutorial - https://learnpython.org
   Free interactive Python tutorial for beginners.
   
3. Python Course - Real Python - https://realpython.com
   Comprehensive Python tutorials and articles.
"""
        
        provider = MCPSearchProvider(mock_brave_search, "brave-mcp")
        results = provider.search("python tutorial", max_results=3)
        
        assert provider.name == "brave-mcp"
        assert len(results) == 3
        assert results[0]["title"] == "Python Tutorial - Official Documentation"
        assert results[0]["url"] == "https://docs.python.org"
        assert "official Python tutorial" in results[0]["snippet"]
    
    def test_mcp_provider_with_dict_response(self):
        """Test MCP provider with dictionary response format."""
        # Mock MCP tool that returns dict (common format)
        def mock_mcp_search(query, count=10):
            return {
                "results": [
                    {
                        "title": "First Result",
                        "url": "https://example.com/1",
                        "snippet": "This is the first result"
                    },
                    {
                        "title": "Second Result",
                        "url": "https://example.com/2",
                        "description": "This is the second result"  # Different field name
                    }
                ]
            }
        
        provider = MCPSearchProvider(mock_mcp_search)
        results = provider.search("test", max_results=2)
        
        assert len(results) == 2
        assert results[0]["snippet"] == "This is the first result"
        assert results[1]["snippet"] == "This is the second result"
    
    def test_mcp_provider_with_web_format(self):
        """Test MCP provider with Brave-style web format."""
        # Mock Brave Search format
        def mock_brave_mcp(query, count=10):
            return {
                "web": {
                    "results": [
                        {
                            "title": "Brave Result 1",
                            "url": "https://brave.com/1",
                            "description": "Brave search result"
                        }
                    ]
                }
            }
        
        provider = MCPSearchProvider(mock_brave_mcp)
        results = provider.search("test")
        
        assert len(results) == 1
        assert results[0]["title"] == "Brave Result 1"
        assert results[0]["snippet"] == "Brave search result"
    
    def test_mcp_provider_with_list_response(self):
        """Test MCP provider with direct list response."""
        # Mock MCP tool that returns list
        def mock_list_search(query, max_results=10):
            return [
                {"title": "Result 1", "url": "http://test1.com", "snippet": "Test 1"},
                {"title": "Result 2", "url": "http://test2.com", "snippet": "Test 2"}
            ]
        
        provider = MCPSearchProvider(mock_list_search)
        results = provider.search("test")
        
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[1]["title"] == "Result 2"
    
    def test_mcp_provider_max_results(self):
        """Test that max_results is respected."""
        def mock_search(query, count=10):
            return {
                "results": [
                    {"title": f"Result {i}", "url": f"http://test{i}.com", "snippet": f"Test {i}"}
                    for i in range(10)
                ]
            }
        
        provider = MCPSearchProvider(mock_search)
        results = provider.search("test", max_results=3)
        
        assert len(results) == 3
    
    def test_mcp_provider_error_handling(self):
        """Test error handling in MCP provider."""
        def faulty_mcp_tool(query, count=10):
            raise Exception("MCP tool error")
        
        provider = MCPSearchProvider(faulty_mcp_tool)
        
        with pytest.raises(Exception) as exc_info:
            provider.search("test")
        
        assert "MCP search failed" in str(exc_info.value)
    
    def test_mcp_provider_parameter_variants(self):
        """Test different parameter name handling."""
        call_count = 0
        
        # Mock that only accepts 'max_results' parameter
        def mock_with_max_results(query, max_results=10):
            nonlocal call_count
            call_count += 1
            return {"results": []}
        
        provider = MCPSearchProvider(mock_with_max_results)
        provider.search("test", max_results=5)
        
        assert call_count == 1  # Should succeed with max_results parameter


class TestCreateMCPSearchProvider:
    """Test the create_mcp_search_provider helper."""
    
    def test_create_provider_finds_tool(self):
        """Test that helper finds MCP tool by name."""
        # Mock tools list
        def brave_search(query, count=10):
            return {"results": []}
        brave_search.__name__ = "brave_search"
        
        def other_tool():
            pass
        other_tool.__name__ = "other_tool"
        
        tools = [other_tool, brave_search]
        
        provider = create_mcp_search_provider("brave_search", tools)
        
        assert provider is not None
        assert provider.name == "brave-mcp"
    
    def test_create_provider_returns_none_if_not_found(self):
        """Test that helper returns None if tool not found."""
        tools = []
        
        provider = create_mcp_search_provider("nonexistent_tool", tools)
        
        assert provider is None
    
    def test_create_provider_names(self):
        """Test that provider names are set correctly."""
        # Test brave naming
        def brave_search():
            return []
        brave_search.__name__ = "brave_search"
        
        provider = create_mcp_search_provider("brave_search", [brave_search])
        assert provider.name == "brave-mcp"
        
        # Test tavily naming
        def tavily_search():
            return []
        tavily_search.__name__ = "tavily_search"
        
        provider = create_mcp_search_provider("tavily_search", [tavily_search])
        assert provider.name == "tavily-mcp"
        
        # Test generic naming
        def custom_search():
            return []
        custom_search.__name__ = "custom_search"
        
        provider = create_mcp_search_provider("custom_search", [custom_search])
        assert provider.name == "custom_search-mcp"