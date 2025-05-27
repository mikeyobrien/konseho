"""Tests for search tool."""

import os
from unittest.mock import patch

import pytest

from konseho.tools.search_ops import MockSearchProvider, SearchProvider, web_search


class TestSearchProvider:
    """Test the SearchProvider base class."""
    
    def test_base_provider_not_implemented(self):
        """Test that base provider raises NotImplementedError."""
        provider = SearchProvider()
        
        with pytest.raises(NotImplementedError):
            provider.search("test query")
    
    def test_base_provider_name(self):
        """Test that base provider has name property."""
        provider = SearchProvider()
        assert provider.name == "base"


class TestMockSearchProvider:
    """Test the MockSearchProvider."""
    
    def test_mock_provider_search(self):
        """Test mock provider returns expected format."""
        provider = MockSearchProvider()
        results = provider.search("test query")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check result format
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            assert isinstance(result["title"], str)
            assert isinstance(result["url"], str)
            assert isinstance(result["snippet"], str)
    
    def test_mock_provider_different_queries(self):
        """Test mock provider returns different results for different queries."""
        provider = MockSearchProvider()
        
        results1 = provider.search("python programming")
        results2 = provider.search("javascript tutorial")
        
        # Should have different content
        assert results1[0]["title"] != results2[0]["title"]
        assert "python" in results1[0]["title"].lower()
        assert "javascript" in results2[0]["title"].lower()
    
    def test_mock_provider_max_results(self):
        """Test mock provider respects max_results parameter."""
        provider = MockSearchProvider()
        
        results = provider.search("test", max_results=2)
        assert len(results) == 2
        
        results = provider.search("test", max_results=5)
        assert len(results) == 5
    
    def test_mock_provider_name(self):
        """Test mock provider name."""
        provider = MockSearchProvider()
        assert provider.name == "mock"


class TestWebSearch:
    """Test the web_search tool function."""
    
    def test_search_with_default_provider(self):
        """Test search with default (mock) provider."""
        results = web_search("test query")
        
        assert "results" in results
        assert "provider" in results
        assert "query" in results
        assert "error" not in results
        
        assert results["provider"] == "mock"
        assert results["query"] == "test query"
        assert isinstance(results["results"], list)
        assert len(results["results"]) > 0
    
    def test_search_with_max_results(self):
        """Test search with max_results parameter."""
        results = web_search("test query", max_results=3)
        
        assert len(results["results"]) == 3
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        results = web_search("")
        
        assert "error" in results
        assert "empty" in results["error"].lower()
    
    def test_search_with_custom_provider(self):
        """Test search with custom provider."""
        # Create a custom provider
        class CustomProvider(SearchProvider):
            @property
            def name(self):
                return "custom"
            
            def search(self, query, max_results=10):
                return [{"title": "Custom", "url": "http://custom.com", "snippet": "Custom result"}]
        
        custom_provider = CustomProvider()
        results = web_search("test", provider=custom_provider)
        
        assert results["provider"] == "custom"
        assert len(results["results"]) == 1
        assert results["results"][0]["title"] == "Custom"
    
    @patch.dict(os.environ, {"SEARCH_PROVIDER": "TAVILY"})
    def test_unsupported_provider_env(self):
        """Test handling of unsupported provider from environment."""
        results = web_search("test query")
        
        # Should fall back to mock with a note
        assert results["provider"] == "mock"
        assert "note" in results
        assert "not configured" in results["note"].lower()
    
    def test_provider_error_handling(self):
        """Test handling of provider errors."""
        # Create a faulty provider
        class FaultyProvider(SearchProvider):
            @property
            def name(self):
                return "faulty"
            
            def search(self, query, max_results=10):
                raise Exception("Provider error")
        
        faulty_provider = FaultyProvider()
        results = web_search("test", provider=faulty_provider)
        
        assert "error" in results
        assert "Provider error" in results["error"]
    
    def test_search_result_format(self):
        """Test that search results have expected format."""
        results = web_search("python tutorial")
        
        assert "results" in results
        for result in results["results"]:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            
            # URLs should be valid
            assert result["url"].startswith("http")
            
            # Content should be non-empty
            assert len(result["title"]) > 0
            assert len(result["snippet"]) > 0