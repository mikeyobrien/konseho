#!/usr/bin/env python3
"""
Example: MCP Configuration and Tool Selection

This example demonstrates:
1. Setting up MCP servers from mcp.json configuration
2. Runtime tool selection with different filtering options
3. Creating personas with MCP-provided tools
4. Using presets for common tool combinations
"""

import asyncio
import json
import tempfile
from pathlib import Path

from konseho import Agent, Council, DebateStep
from konseho.mcp import MCP


async def setup_example_mcp_config():
    """Create an example mcp.json configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "mcp.json"
        
        # Example configuration compatible with Cline/Claude Code
        config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", tmpdir],
                    "description": "File system operations"
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_TOKEN": "${GITHUB_TOKEN}"  # Environment variable reference
                    },
                    "description": "GitHub API operations"
                },
                "web-search": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {
                        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
                    },
                    "description": "Web search capabilities"
                },
                "python-repl": {
                    "command": "python",
                    "args": ["-m", "mcp.server.python"],
                    "description": "Python code execution"
                }
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"Created example mcp.json at: {config_path}")
        return config_path


async def example_runtime_tool_selection():
    """Demonstrate runtime tool selection."""
    print("\n=== Runtime Tool Selection Example ===\n")
    
    # Create MCP configuration
    config_path = await setup_example_mcp_config()
    mcp = MCP(config_path)
    
    # Start specific servers
    print("Starting filesystem and web-search servers...")
    results = await mcp.start_servers(["filesystem", "web-search"])
    print(f"Server startup results: {results}")
    
    # Example 1: Select specific tools by name
    print("\n1. Selecting specific tools by name:")
    tools = await mcp.get_tools(tools=["file_read", "file_write", "web_search"])
    print(f"   Selected {len(tools)} tools: {[t.__name__ for t in tools]}")
    
    # Example 2: Select all tools from a specific server
    print("\n2. Selecting all tools from filesystem server:")
    tools = await mcp.get_tools(servers=["filesystem"])
    print(f"   Selected {len(tools)} tools: {[t.__name__ for t in tools]}")
    
    # Example 3: Select tools by tags
    print("\n3. Selecting tools by tags:")
    tools = await mcp.get_tools(tags=["file", "io"])
    print(f"   Selected {len(tools)} tools: {[t.__name__ for t in tools]}")
    
    # Example 4: Use preset for common personas
    print("\n4. Using presets for personas:")
    
    # Coder preset
    coder_tools = await mcp.get_tools(preset="coder")
    print(f"   Coder preset: {len(coder_tools)} tools")
    
    # Researcher preset
    researcher_tools = await mcp.get_tools(preset="researcher")
    print(f"   Researcher preset: {len(researcher_tools)} tools")
    
    # Analyst preset
    analyst_tools = await mcp.get_tools(preset="analyst")
    print(f"   Analyst preset: {len(analyst_tools)} tools")
    
    # Clean up
    await mcp.stop_all_servers()


async def example_persona_with_mcp_tools():
    """Create personas with MCP-provided tools."""
    print("\n=== Persona with MCP Tools Example ===\n")
    
    # Create MCP configuration
    config_path = await setup_example_mcp_config()
    mcp = MCP(config_path)
    
    # Start servers
    await mcp.start_servers(["filesystem", "web-search", "python-repl"])
    
    # Create a research analyst with specific tools
    analyst_tools = await mcp.get_tools(
        tools=["file_read", "web_search", "python_execute"],
        servers=["filesystem", "web-search", "python-repl"]
    )
    
    analyst = Agent(
        "Research Analyst",
        "You analyze data and create reports. Use web search to find information, "
        "python to analyze data, and file operations to save results.",
        tools=analyst_tools
    )
    
    # Create a code reviewer with different tools
    reviewer_tools = await mcp.get_tools(preset="coder")
    
    reviewer = Agent(
        "Code Reviewer",
        "You review code for quality and suggest improvements. "
        "Use file operations to read code and provide feedback.",
        tools=reviewer_tools
    )
    
    # Create a council with these specialized agents
    council = Council(
        agents=[analyst, reviewer],
        steps=[
            DebateStep(
                "Research the topic and review any code examples",
                participants=["Research Analyst", "Code Reviewer"]
            )
        ]
    )
    
    # Example task (would need mock MCP servers for actual execution)
    print("Created council with MCP-enabled agents:")
    print(f"- Analyst tools: {[t.__name__ for t in analyst_tools]}")
    print(f"- Reviewer tools: {[t.__name__ for t in reviewer_tools]}")
    
    # Clean up
    await mcp.stop_all_servers()


async def example_dynamic_tool_loading():
    """Demonstrate dynamic tool loading based on task."""
    print("\n=== Dynamic Tool Loading Example ===\n")
    
    # Create MCP configuration
    config_path = await setup_example_mcp_config()
    mcp = MCP(config_path)
    
    # Function to create agent with tools based on task
    async def create_agent_for_task(task_type: str) -> Agent:
        """Create an agent with appropriate tools for the task."""
        if task_type == "web_research":
            # Start web search server if not already running
            await mcp.start_servers(["web-search"])
            tools = await mcp.get_tools(servers=["web-search"])
            return Agent(
                "Web Researcher",
                "You excel at finding and synthesizing information from the web.",
                tools=tools
            )
        
        elif task_type == "code_analysis":
            # Start filesystem and python servers
            await mcp.start_servers(["filesystem", "python-repl"])
            tools = await mcp.get_tools(
                tools=["file_read", "file_list", "python_execute"],
                servers=["filesystem", "python-repl"]
            )
            return Agent(
                "Code Analyst",
                "You analyze code structure and quality.",
                tools=tools
            )
        
        elif task_type == "documentation":
            # Start filesystem server only
            await mcp.start_servers(["filesystem"])
            tools = await mcp.get_tools(
                tools=["file_read", "file_write", "file_list"],
                servers=["filesystem"]
            )
            return Agent(
                "Documentation Writer",
                "You create clear and comprehensive documentation.",
                tools=tools
            )
        
        else:
            # Default agent with no special tools
            return Agent(
                "General Assistant",
                "You help with general tasks."
            )
    
    # Demonstrate creating agents for different tasks
    tasks = ["web_research", "code_analysis", "documentation"]
    
    for task_type in tasks:
        print(f"\nCreating agent for {task_type}:")
        agent = await create_agent_for_task(task_type)
        print(f"  Agent: {agent._name}")
        print(f"  Tools: {len(agent._tools) if hasattr(agent, '_tools') else 0}")
    
    # Clean up
    await mcp.stop_all_servers()


async def example_tool_composition():
    """Show how to compose tools from multiple sources."""
    print("\n=== Tool Composition Example ===\n")
    
    # Create MCP configuration
    config_path = await setup_example_mcp_config()
    mcp = MCP(config_path)
    
    # Start all servers
    await mcp.start_servers(["filesystem", "github", "web-search"])
    
    # Compose tools for a full-stack developer
    print("Composing tools for a Full-Stack Developer:")
    
    # Get file operations
    file_tools = await mcp.get_tools(
        tools=["file_read", "file_write", "file_list"],
        servers=["filesystem"]
    )
    print(f"  File tools: {[t.__name__ for t in file_tools]}")
    
    # Get GitHub operations
    github_tools = await mcp.get_tools(
        tools=["create_issue", "create_pr", "review_pr"],
        servers=["github"]
    )
    print(f"  GitHub tools: {[t.__name__ for t in github_tools]}")
    
    # Get research tools
    research_tools = await mcp.get_tools(
        servers=["web-search"]
    )
    print(f"  Research tools: {[t.__name__ for t in research_tools]}")
    
    # Combine all tools
    all_tools = file_tools + github_tools + research_tools
    
    developer = Agent(
        "Full-Stack Developer",
        "You build complete applications, manage code on GitHub, "
        "and research best practices.",
        tools=all_tools
    )
    
    print(f"\nCreated developer with {len(all_tools)} total tools")
    
    # Clean up
    await mcp.stop_all_servers()


if __name__ == "__main__":
    async def main():
        """Run all examples."""
        await example_runtime_tool_selection()
        await example_persona_with_mcp_tools()
        await example_dynamic_tool_loading()
        await example_tool_composition()
    
    asyncio.run(main())