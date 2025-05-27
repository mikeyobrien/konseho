"""Example of using generic MCP tools with Konseho agents."""


from konseho.agents.base import AgentWrapper, create_agent
from konseho.factories import CouncilFactory
from konseho.core.steps import ParallelStep
from konseho.tools.mcp_adapter import MCPToolAdapter, adapt_mcp_tools, create_mcp_tool

# Simulated MCP tools for demonstration
# In practice, these come from MCP servers via:
# claude mcp add <server-name> <command>

def github_mcp_search_repos(query: str, limit: int = 10) -> str:
    """Mock GitHub MCP tool - search repositories."""
    return f"""Found {limit} repositories matching '{query}':

1. awesome-{query} - A curated list of {query} resources
   ⭐ 15,234 | 🍴 2,341 | Language: Markdown
   
2. {query}-tutorial - Complete tutorial for {query}
   ⭐ 8,123 | 🍴 1,234 | Language: Python
   
3. {query}-examples - Example code for {query}
   ⭐ 5,432 | 🍴 892 | Language: JavaScript

Total results: 1,234 repositories"""


def filesystem_mcp_list_files(path: str = ".", pattern: str = "*") -> str:
    """Mock filesystem MCP tool - list files."""
    return f"""Files in {path} matching '{pattern}':
- README.md (2.3 KB)
- src/
  - main.py (5.1 KB)
  - utils.py (3.2 KB)
  - config.json (1.1 KB)
- tests/
  - test_main.py (4.5 KB)
  - test_utils.py (2.8 KB)
- requirements.txt (0.5 KB)

Total: 6 files, 2 directories"""


def slack_mcp_post_message(channel: str, message: str) -> str:
    """Mock Slack MCP tool - post message."""
    return f"""Message posted to #{channel}:
Status: Success
Timestamp: 2024-01-15 10:30:45
Message ID: msg_12345
Reactions: []"""


def weather_mcp_get_forecast(location: str, days: int = 3) -> str:
    """Mock weather MCP tool - get forecast."""
    return f"""Weather forecast for {location} ({days} days):

Day 1: Sunny, 72°F (22°C), 10% rain
Day 2: Partly cloudy, 68°F (20°C), 20% rain  
Day 3: Rainy, 65°F (18°C), 80% rain

Updated: 2024-01-15 10:00 UTC"""


def demo_generic_mcp_adapter():
    """Demonstrate generic MCP tool adaptation."""
    
    print("=== Generic MCP Tool Adapter Demo ===\n")
    
    # Example 1: Manual wrapping of individual tools
    print("1. Manual MCP Tool Wrapping:")
    print("-" * 60)
    
    # Wrap GitHub MCP tool
    github_tool = MCPToolAdapter(github_mcp_search_repos, "github_search")
    
    # Use the wrapped tool
    result = github_tool("python async", limit=5)
    print(f"Tool: {github_tool.name}")
    print(f"Response type: {type(result)}")
    print(f"Processed response: {result}\n")
    
    # Example 2: Automatic adaptation of multiple tools
    print("\n2. Automatic MCP Tool Adaptation:")
    print("-" * 60)
    
    # Simulate MCP tools with naming convention
    github_mcp_search_repos.__name__ = "github_mcp_search"
    filesystem_mcp_list_files.__name__ = "fs_mcp_list"
    slack_mcp_post_message.__name__ = "slack_post"
    weather_mcp_get_forecast.__name__ = "weather_forecast"
    
    # Mix of MCP and regular tools
    all_tools = [
        github_mcp_search_repos,  # MCP tool
        filesystem_mcp_list_files,  # MCP tool
        slack_mcp_post_message,  # Regular tool (no mcp in name)
        weather_mcp_get_forecast,  # Regular tool
    ]
    
    # Adapt only MCP tools automatically
    adapted_tools = adapt_mcp_tools(all_tools)
    
    print("Adapted tools:")
    for tool in adapted_tools:
        if isinstance(tool, MCPToolAdapter):
            print(f"  ✓ {tool.name} (wrapped)")
        else:
            print(f"  - {tool.__name__} (unchanged)")
    
    # Example 3: Create custom MCP tools with metadata
    print("\n\n3. Custom MCP Tool Creation:")
    print("-" * 60)
    
    # Create a well-documented MCP tool
    database_tool = create_mcp_tool(
        name="query_database",
        description="Query the database using natural language",
        mcp_function=lambda query: f"Results for '{query}':\n- User count: 1,234\n- Active: 89%"
    )
    
    print(f"Tool name: {database_tool.__name__}")
    print(f"Tool docs: {database_tool.__doc__}")
    
    # Example 4: Agent with adapted MCP tools
    print("\n\n4. Agent with Adapted MCP Tools:")
    print("-" * 60)
    
    # Create agent with adapted tools
    researcher = create_agent(
        name="MCP Researcher",
        system_prompt="""You are a researcher with access to various MCP tools.
        Use github_search to find code, fs_mcp_list to explore files,
        and weather_forecast to check conditions.""",
        tools=[
            MCPToolAdapter(github_mcp_search_repos),
            MCPToolAdapter(filesystem_mcp_list_files),
            MCPToolAdapter(weather_mcp_get_forecast),
        ]
    )
    
    print("Agent created with MCP tools:")
    for tool in researcher.tools:
        if hasattr(tool, '__name__'):
            print(f"  - {tool.__name__}")
    
    # Example 5: Multi-agent council with MCP tools
    print("\n\n5. Multi-Agent Council with MCP Tools:")
    print("-" * 60)
    
    # Create specialized agents with different MCP tools
    code_researcher = AgentWrapper(
        create_agent(
            name="Code Researcher",
            system_prompt="Search for code examples and repositories.",
            tools=[MCPToolAdapter(github_mcp_search_repos)]
        ),
        name="Code Researcher"
    )
    
    file_explorer = AgentWrapper(
        create_agent(
            name="File Explorer",
            system_prompt="Explore file systems and analyze structure.",
            tools=[MCPToolAdapter(filesystem_mcp_list_files)]
        ),
        name="File Explorer"
    )
    
    # Create council
    factory = CouncilFactory()

    research_council = factory.create_council(
        name="MCP Research Council",
        steps=[
            ParallelStep(
                agents=[code_researcher, file_explorer],
                task_splitter=lambda task, n: [
                    f"Search GitHub for: {task}",
                    f"Explore local files related to: {task}"
                ]
            )
        ]
    )
    
    print("Created council with MCP-enabled agents")
    
    # Example 6: Response processing demonstration
    print("\n\n6. MCP Response Processing:")
    print("-" * 60)
    
    # Show how different response types are handled
    test_responses = [
        '{"status": "ok", "count": 5}',  # JSON string
        "1. First item\n2. Second item\n3. Third item",  # Numbered list
        "Name: John Doe\nAge: 30\nRole: Developer",  # Key-value format
        "Just a plain text response",  # Plain text
    ]
    
    adapter = MCPToolAdapter(lambda: None, "test_tool")
    
    for i, response in enumerate(test_responses, 1):
        processed = adapter._process_response(response)
        print(f"\nResponse {i}:")
        print(f"  Original: {response[:50]}...")
        print(f"  Processed type: {processed.get('type', type(processed).__name__)}")
    
    print("\n" + "="*60)
    print("Summary: MCP Tool Integration")
    print("="*60)
    print("1. MCPToolAdapter wraps any MCP tool for better agent compatibility")
    print("2. adapt_mcp_tools() automatically identifies and wraps MCP tools")
    print("3. create_mcp_tool() creates well-documented wrapped tools")
    print("4. Response processing converts strings to structured data")
    print("5. Works seamlessly with agents and councils")
    print("\nTo use real MCP tools:")
    print("1. Add MCP servers: claude mcp add <name> <command>")
    print("2. Wrap tools: adapted = adapt_mcp_tools(agent.tools)")
    print("3. Use in agents as normal tools")


if __name__ == "__main__":
    demo_generic_mcp_adapter()