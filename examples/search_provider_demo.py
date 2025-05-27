#!/usr/bin/env python3
"""
Comprehensive demo of search provider integration in Konseho.

This example shows:
1. Using mock/fake search provider for testing
2. Integrating MCP search servers (brave-search, tavily, etc.)
3. Creating custom search providers
4. Dynamic provider selection based on configuration
"""

import asyncio
import os

# from konseho.mcp.config import MCPConfig  # Not needed for this demo
from strands import tool

from konseho.agents.base import AgentWrapper, create_agent
from konseho.core.council import Council
from konseho.core.steps import ParallelStep
from konseho.tools.file_ops import file_write
from konseho.tools.mcp_search_adapter import (
    MCPSearchProvider,
)
from konseho.tools.search_ops import MockSearchProvider, SearchProvider, web_search


class FakeNewsSearchProvider(SearchProvider):
    """A fake search provider that returns news-style results for testing."""
    
    @property
    def name(self) -> str:
        return "fake-news"
    
    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        """Generate fake news-style search results."""
        # Create realistic-looking news results
        base_results = [
            {
                "title": f"Breaking: {query.title()} Revolutionizes Industry",
                "url": f"https://technews.example.com/2024/breaking-{query.replace(' ', '-').lower()}",
                "snippet": f"In a stunning development, experts say {query} is transforming how businesses operate..."
            },
            {
                "title": f"How {query.title()} is Changing Everything in 2024",
                "url": f"https://forbes.example.com/tech/{query.replace(' ', '-').lower()}-guide",
                "snippet": f"Industry leaders reveal why {query} is the most important trend this year..."
            },
            {
                "title": f"The Complete Guide to {query.title()}",
                "url": f"https://medium.example.com/@tech/{query.replace(' ', '-').lower()}-explained",
                "snippet": f"Everything you need to know about {query}, explained by experts in simple terms..."
            },
            {
                "title": f"5 Things You Didn't Know About {query.title()}",
                "url": f"https://buzztech.example.com/{query.replace(' ', '-').lower()}-facts",
                "snippet": f"Surprising facts about {query} that will change your perspective..."
            },
            {
                "title": f"{query.title()}: Expert Analysis and Future Predictions",
                "url": f"https://analyst.example.com/reports/{query.replace(' ', '-').lower()}-2024",
                "snippet": f"Top analysts share their insights on where {query} is heading in the next 5 years..."
            }
        ]
        
        return base_results[:max_results]


class FakeAcademicSearchProvider(SearchProvider):
    """A fake search provider that returns academic-style results for testing."""
    
    @property 
    def name(self) -> str:
        return "fake-academic"
    
    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        """Generate fake academic-style search results."""
        base_results = [
            {
                "title": f"A Systematic Review of {query.title()} in Modern Applications",
                "url": f"https://arxiv.example.org/abs/2024.{query.replace(' ', '').lower()}",
                "snippet": f"We present a comprehensive survey of {query} techniques, analyzing 127 papers..."
            },
            {
                "title": f"Novel Approaches to {query.title()}: A Machine Learning Perspective",
                "url": f"https://papers.example.edu/ml/{query.replace(' ', '-').lower()}.pdf",
                "snippet": f"This paper introduces three novel algorithms for {query} that outperform baselines..."
            },
            {
                "title": f"Theoretical Foundations of {query.title()}",
                "url": f"https://journal.example.org/theory/{query.replace(' ', '-').lower()}",
                "snippet": f"We establish the mathematical foundations for {query} and prove several key theorems..."
            }
        ]
        
        return base_results[:max_results]


def get_search_provider(provider_name: str | None = None) -> SearchProvider:
    """
    Get a search provider based on name or environment configuration.
    
    This demonstrates the pattern users should follow:
    1. Check for MCP tools if available
    2. Check for API-based providers with keys
    3. Fall back to mock/fake providers for testing
    """
    if not provider_name:
        provider_name = os.environ.get("SEARCH_PROVIDER", "mock")
    
    provider_name = provider_name.lower()
    
    # MCP-based providers (would come from actual MCP servers)
    if provider_name.startswith("mcp-"):
        # In production, this would use actual MCP tools
        # For demo, we'll simulate it
        if provider_name == "mcp-brave":
            # Simulate MCP brave_search tool
            def mock_brave_search(query: str, count: int = 10) -> str:
                return f"""Found {count} results for "{query}":
1. Understanding {query} - Brave Search Result - https://example.com/1
   Comprehensive overview of {query} from verified sources...
   
2. {query} Best Practices - Brave Search Result - https://example.com/2  
   Industry standards and recommendations for implementing {query}...
   
3. Latest {query} News - Brave Search Result - https://example.com/3
   Breaking developments and updates about {query}..."""
            
            return MCPSearchProvider(mock_brave_search, "mcp-brave")
    
    # API-based providers (would use real APIs with keys)
    elif provider_name == "brave":
        api_key = os.environ.get("BRAVE_API_KEY")
        if api_key:
            # In production: return BraveSearchProvider(api_key)
            print(f"[Would use Brave Search API with key: {api_key[:8]}...]")
        return MockSearchProvider()  # Fallback to mock
    
    elif provider_name == "tavily":
        api_key = os.environ.get("TAVILY_API_KEY")
        if api_key:
            # In production: return TavilySearchProvider(api_key)
            print(f"[Would use Tavily API with key: {api_key[:8]}...]")
        return MockSearchProvider()  # Fallback to mock
    
    # Fake providers for testing
    elif provider_name == "fake-news":
        return FakeNewsSearchProvider()
    
    elif provider_name == "fake-academic":
        return FakeAcademicSearchProvider()
    
    # Default mock provider
    else:
        return MockSearchProvider()


async def demo_search_providers():
    """Demonstrate different search provider configurations."""
    
    print("="*60)
    print("Konseho Search Provider Demo")
    print("="*60)
    
    # Demo 1: Using different fake providers
    print("\n1. Fake Provider Examples")
    print("-"*40)
    
    # News-style search
    news_provider = FakeNewsSearchProvider()
    news_results = web_search("artificial intelligence", provider=news_provider)
    print(f"\nNews Search ({news_provider.name}):")
    for i, result in enumerate(news_results['results'][:2], 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet'][:80]}...")
    
    # Academic-style search  
    academic_provider = FakeAcademicSearchProvider()
    academic_results = web_search("quantum computing", provider=academic_provider)
    print(f"\nAcademic Search ({academic_provider.name}):")
    for i, result in enumerate(academic_results['results'][:2], 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet'][:80]}...")
    
    # Demo 2: Configuration-based provider selection
    print("\n\n2. Configuration-Based Provider Selection")
    print("-"*40)
    
    # Check environment
    current_provider = os.environ.get("SEARCH_PROVIDER", "mock")
    print(f"Current SEARCH_PROVIDER: {current_provider}")
    
    # Get provider based on configuration
    provider = get_search_provider()
    print(f"Selected provider: {provider.name}")
    
    results = web_search("konseho multi-agent", provider=provider)
    print(f"\nSearch results using {provider.name}:")
    for result in results['results'][:2]:
        print(f"- {result['title']}")
    
    # Demo 3: MCP integration simulation
    print("\n\n3. MCP Search Integration (Simulated)")
    print("-"*40)
    
    # Simulate having MCP tools available
    def brave_search(query: str, count: int = 10) -> str:
        """Simulated MCP brave_search tool."""
        return f"""Search results for "{query}":
1. {query.title()} Documentation - https://docs.example.com
2. Getting Started with {query.title()} - https://tutorial.example.com  
3. {query.title()} Best Practices - https://guide.example.com"""
    
    # Create MCP provider
    mcp_provider = MCPSearchProvider(brave_search, "brave-mcp")
    print(f"Created MCP provider: {mcp_provider.name}")
    
    # Use it for search
    mcp_results = web_search("strands agent sdk", provider=mcp_provider)
    print("\nMCP Search Results:")
    for result in mcp_results['results']:
        print(f"- {result['title']}")
    
    # Demo 4: Multi-agent council with different providers
    print("\n\n4. Multi-Agent Council with Different Search Providers")
    print("-"*60)
    
    # Create search functions with different providers
    @tool
    def search_news(query: str) -> dict:
        """Search for news and current events."""
        return web_search(query, provider=FakeNewsSearchProvider())
    
    @tool
    def search_academic(query: str) -> dict:
        """Search for academic papers and research."""
        return web_search(query, provider=FakeAcademicSearchProvider())
    
    # Create specialized agents
    news_researcher = AgentWrapper(
        create_agent(
            name="News Researcher",
            system_prompt="You research current news and trends. Use search_news for information.",
            tools=[search_news, file_write]
        ),
        name="News Researcher"
    )
    
    academic_researcher = AgentWrapper(
        create_agent(
            name="Academic Researcher",
            system_prompt="You research academic papers. Use search_academic for scholarly sources.",
            tools=[search_academic, file_write]
        ),
        name="Academic Researcher"
    )
    
    # Create research council
    council = Council(
        name="Mixed Research Council",
        steps=[
            ParallelStep(
                agents=[news_researcher, academic_researcher],
                task_splitter=lambda task, n: [
                    f"Find recent news about {task}",
                    f"Find academic research on {task}"
                ]
            )
        ]
    )
    
    # Execute research task
    topic = "large language models"
    print(f"\nResearching: {topic}")
    print("Council is gathering information from different sources...")
    
    result = await council.execute(topic)
    print("\n✅ Research complete!")
    
    # Demo 5: Provider switching
    print("\n\n5. Dynamic Provider Switching")
    print("-"*40)
    
    providers = {
        "news": FakeNewsSearchProvider(),
        "academic": FakeAcademicSearchProvider(), 
        "general": MockSearchProvider()
    }
    
    for name, provider in providers.items():
        results = web_search("python programming", provider=provider, max_results=1)
        print(f"\n{name.title()} search ({provider.name}):")
        if results['results']:
            print(f"  {results['results'][0]['title']}")
    
    # Summary
    print("\n\n" + "="*60)
    print("Summary: Search Provider Integration")
    print("="*60)
    print("""
1. Fake/Mock Providers: Perfect for testing without API keys
   - MockSearchProvider: General purpose testing
   - Custom fake providers: Domain-specific testing (news, academic, etc.)

2. MCP Integration: Use search tools from MCP servers
   - Wrap MCP tools with MCPSearchProvider
   - Automatic detection with create_mcp_search_provider()
   - Works with brave-search, tavily, and other MCP search servers

3. API Providers: Direct integration with search APIs
   - Implement custom SearchProvider subclasses
   - Use environment variables for API keys
   - Examples: Brave, Tavily, Serper, etc.

4. Configuration: Flexible provider selection
   - Environment variables (SEARCH_PROVIDER)
   - Runtime selection based on task
   - Different providers for different agents

5. Best Practices:
   - Start with mock providers for development
   - Use MCP when tools are available
   - Fall back gracefully when APIs unavailable
   - Let agents specialize with different providers
""")


if __name__ == "__main__":
    asyncio.run(demo_search_providers())