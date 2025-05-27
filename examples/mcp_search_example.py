"""Example of using MCP search servers with Konseho agents."""

from konseho.agents.base import AgentWrapper, create_agent
from konseho.core.council import Council
from konseho.core.steps import ParallelStep
from konseho.tools.file_ops import file_write
from konseho.tools.mcp_search_adapter import (
    MCPSearchProvider,
    create_mcp_search_provider,
)
from konseho.tools.search_ops import web_search


def demo_mcp_search_integration():
    """Demonstrate how to integrate MCP search with Konseho agents."""
    
    # Simulate having MCP tools available (in practice, these come from MCP servers)
    # For demo, we'll create a mock MCP search tool
    def brave_search(query: str, count: int = 10) -> str:
        """Mock Brave Search MCP tool for demonstration."""
        # In reality, this would be provided by:
        # claude mcp add brave-search npx @modelcontextprotocol/server-brave-search
        return f"""Search results for "{query}":

1. Understanding {query} - A Comprehensive Guide - https://guide.example.com/{query.replace(' ', '-')}
   Everything you need to know about {query}, from basics to advanced topics.

2. {query.title()} Best Practices 2024 - https://bestpractices.example.com/{query.replace(' ', '-')}
   Industry standards and recommendations for {query} implementation.

3. Troubleshooting {query} Issues - https://debug.example.com/{query.replace(' ', '-')}
   Common problems and solutions when working with {query}.
"""
    
    # Mark it as an MCP tool
    brave_search.__name__ = "brave_search"
    
    # Create an agent with MCP tool and our search wrapper
    print("Setting up Research Agent with MCP search...")
    
    # Create MCP search provider
    mcp_provider = MCPSearchProvider(brave_search, "brave-mcp")
    
    # Create a bound search function that uses MCP
    def search_with_mcp(query: str, max_results: int = 10):
        """Search using MCP Brave Search."""
        return web_search(query, max_results=max_results, provider=mcp_provider)
    
    # Create research agent with MCP-powered search
    researcher = create_agent(
        name="Researcher",
        system_prompt="""You are a research assistant. Use the search_with_mcp tool 
        to find information and the file_write tool to save important findings.""",
        tools=[search_with_mcp, file_write]
    )
    
    # Example 1: Direct search
    print("\n1. Direct Search Example:")
    print("-" * 60)
    
    search_results = search_with_mcp("python async programming")
    print(f"Provider: {search_results['provider']}")
    print(f"Query: {search_results['query']}")
    print(f"Results found: {len(search_results['results'])}")
    
    for i, result in enumerate(search_results['results'][:3], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   {result['snippet']}")
    
    # Example 2: Multi-agent research with MCP
    print("\n\n2. Multi-Agent Research Council:")
    print("-" * 60)
    
    # Create multiple researchers with different MCP providers
    # (In practice, you might have different MCP search servers)
    
    researcher1 = AgentWrapper(
        create_agent(
            name="Academic Researcher",
            system_prompt="You search for academic and technical information.",
            tools=[search_with_mcp, file_write]
        ),
        name="Academic Researcher"
    )
    
    researcher2 = AgentWrapper(
        create_agent(
            name="Industry Researcher", 
            system_prompt="You search for industry trends and practical applications.",
            tools=[search_with_mcp, file_write]
        ),
        name="Industry Researcher"
    )
    
    # Create research council
    research_council = Council(
        name="MCP Research Council",
        steps=[
            ParallelStep(
                agents=[researcher1, researcher2],
                task_splitter=lambda task, n: [
                    f"Search for academic research on: {task}",
                    f"Search for industry applications of: {task}"
                ]
            )
        ]
    )
    
    # Example 3: Automatic MCP tool detection
    print("\n3. Automatic MCP Tool Detection:")
    print("-" * 60)
    
    # Create agent with multiple tools including MCP
    agent_with_tools = create_agent(
        name="Multi-Tool Agent",
        tools=[brave_search, file_write]  # MCP tool included directly
    )
    
    # Automatically create provider from agent's tools
    auto_provider = create_mcp_search_provider("brave_search", agent_with_tools.tools)
    
    if auto_provider:
        print(f"✓ Found MCP search tool: {auto_provider.name}")
        
        # Use it for search
        results = web_search("konseho patterns", provider=auto_provider)
        print(f"  Searched for: {results['query']}")
        print(f"  Results: {len(results['results'])}")
    else:
        print("✗ No MCP search tool found")
    
    print("\n" + "="*60)
    print("MCP Search Integration Summary:")
    print("="*60)
    print("1. MCP tools can be wrapped as SearchProviders")
    print("2. Agents can use MCP search through web_search()")
    print("3. Multiple MCP providers can work in parallel")
    print("4. Automatic detection simplifies setup")
    print("\nTo use real MCP search:")
    print("1. Install MCP server: claude mcp add brave-search npx @modelcontextprotocol/server-brave-search")
    print("2. The brave_search tool will be available in your agents")
    print("3. Use MCPSearchProvider to wrap it for Konseho")


if __name__ == "__main__":
    demo_mcp_search_integration()