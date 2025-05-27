#!/usr/bin/env python3
"""Example of using real search providers with Konseho."""

import asyncio
import os

from strands import tool

from konseho.agents.base import AgentWrapper, create_agent
from konseho.factories import CouncilFactory
from konseho.core.steps import ParallelStep
from konseho.tools.search_ops import SearchProvider
from konseho.tools.search_ops import web_search as base_web_search
from konseho.tools.search_tool import web_search


# Example implementation of a real search provider
class BraveSearchProvider(SearchProvider):
    """Real Brave Search implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    @property
    def name(self) -> str:
        return "brave"
    
    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        # In a real implementation, you would:
        # 1. Make HTTP request to Brave Search API
        # 2. Parse the response
        # 3. Return normalized results
        
        # For demo purposes, we'll just show the structure
        print(f"[Would search Brave for: '{query}' with API key: {self.api_key[:8]}...]")
        
        # Mock response structure
        return [
            {
                "title": f"Real result 1 for {query}",
                "url": "https://example.com/1",
                "snippet": "This would be real search results from Brave Search API..."
            },
            {
                "title": f"Real result 2 for {query}",
                "url": "https://example.com/2",
                "snippet": "Another real result with actual content..."
            }
        ]


async def main():
    """Demonstrate using real search providers."""
    
    print("=== Real Search Provider Demo ===\n")
    
    # Check for API key
    api_key = os.environ.get("BRAVE_API_KEY")
    
    if api_key:
        print("✅ Found BRAVE_API_KEY in environment")
        print("   Configuring real Brave Search provider...\n")
        
        # Create real search provider
        provider = BraveSearchProvider(api_key)
        
        # Create a search tool that uses this provider
        @tool
        def search_with_brave(query: str, max_results: int = 10) -> dict:
            """Search using Brave Search."""
            return base_web_search(query, max_results, provider=provider)
        
        search_tool = search_with_brave
    else:
        print("ℹ️  No BRAVE_API_KEY found in environment")
        print("   Using mock search provider")
        print("\nTo use real search:")
        print("1. Get an API key from https://brave.com/search/api")
        print("2. Export it: export BRAVE_API_KEY='your-key-here'")
        print("3. Run this example again\n")
        
        # Use default mock search
        search_tool = web_search
        provider = None
    
    # Create agents that use the appropriate search tool
    researcher = AgentWrapper(
        create_agent(
            name="Researcher",
            system_prompt="You are a research assistant. Use search to find current information.",
            tools=[search_tool]
        ),
        name="Researcher"
    )
    
    fact_checker = AgentWrapper(
        create_agent(
            name="Fact Checker",
            system_prompt="You verify facts. Use search to check claims.",
            tools=[search_tool]
        ),
        name="Fact Checker"
    )
    
    # Create a simple council
    factory = CouncilFactory()

    council = factory.create_council(
        name="Research Council",
        steps=[
            ParallelStep(
        agents=[researcher, fact_checker],
                task_splitter=lambda task, n: [
                    f"Research: {task}",
                    f"Verify facts about: {task}"
                ]

    )
        ]
    )
    
    # Run a research task
    task = "the latest developments in quantum computing"
    print(f"📋 Task: Research {task}\n")
    
    result = await council.execute(task)
    
    print("\n✅ Research complete!")
    print(f"   Used search provider: {provider.name if provider else 'mock'}")
    
    # Show how to implement other providers
    print("\n" + "="*50)
    print("Other Search Providers")
    print("="*50)
    print("""
You can implement other search providers similarly:

1. Tavily Search:
   - Get API key from https://tavily.com
   - Implement TavilySearchProvider class
   - Set with: set_search_provider(TavilySearchProvider(api_key))

2. Serper.dev (Google Search):
   - Get API key from https://serper.dev
   - Implement SerperSearchProvider class
   - Set with: set_search_provider(SerperSearchProvider(api_key))

3. Custom internal search:
   - Implement your own SearchProvider
   - Could search internal documents, databases, etc.
""")


if __name__ == "__main__":
    asyncio.run(main())