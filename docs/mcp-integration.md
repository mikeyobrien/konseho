# MCP (Model Context Protocol) Integration

Konseho provides comprehensive integration with MCP servers, allowing you to use any MCP tool within your multi-agent systems with full configuration compatibility.

## Overview

Konseho's MCP integration provides:

- **Configuration Compatibility**: Use the same `mcp.json` format as Cline and Claude Code
- **Runtime Tool Selection**: Choose which tools to attach to agents dynamically
- **Automatic Response Processing**: Convert string responses to structured data
- **Server Lifecycle Management**: Start/stop MCP servers as needed
- **Tool Presets**: Pre-configured tool sets for common agent personas
- **Flexible Filtering**: Select tools by name, server, tags, or custom logic

## Configuration

### mcp.json Format

Konseho uses the same `mcp.json` format as Cline and Claude Code:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"],
      "env": {
        "SOME_VAR": "value"
      },
      "description": "File system operations"
    },
    "github": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Configuration Locations

Konseho looks for `mcp.json` in these locations (in order):
1. Path specified when creating MCP instance
2. Current working directory
3. `~/.config/konseho/mcp.json`
4. `~/.konseho/mcp.json`

## Quick Start

### Basic Usage

```python
from konseho import Agent
from konseho.mcp import MCP

# Create MCP instance (auto-discovers mcp.json)
mcp = MCP()

# Start servers and get tools
await mcp.start_servers(["filesystem", "github"])
tools = await mcp.get_tools()

# Create agent with tools
agent = Agent("Developer", "You write code", tools=tools)
```

### Using Tool Presets

```python
# Get tools for common personas
coder_tools = await mcp.get_tools(preset="coder")
researcher_tools = await mcp.get_tools(preset="researcher")
analyst_tools = await mcp.get_tools(preset="analyst")

# Create specialized agents
coder = Agent("Coder", "You write clean code", tools=coder_tools)
researcher = Agent("Researcher", "You find information", tools=researcher_tools)
```

### Selective Tool Loading

```python
# Select specific tools by name
tools = await mcp.get_tools(tools=["file_read", "file_write", "web_search"])

# Select all tools from specific servers
tools = await mcp.get_tools(servers=["filesystem", "github"])

# Combine multiple filters
tools = await mcp.get_tools(
    tools=["file_read", "web_search"],
    servers=["filesystem", "web-search"],
    tags=["safe", "read-only"]
)
```

## Available MCP Servers

Common MCP servers that work with Konseho:

### File System Access
```bash
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem /path/to/allowed/dir
```

### GitHub Integration
```bash
claude mcp add github npx @modelcontextprotocol/server-github
```

### Web Browsing
```bash
claude mcp add web npx @modelcontextprotocol/server-puppeteer
```

### Search Services
```bash
# Brave Search
claude mcp add brave-search npx @modelcontextprotocol/server-brave-search

# Tavily Search
claude mcp add tavily npx @tavily/mcp-server
```

### Databases
```bash
# PostgreSQL
claude mcp add postgres npx @modelcontextprotocol/server-postgres postgresql://localhost/mydb

# SQLite
claude mcp add sqlite npx @modelcontextprotocol/server-sqlite /path/to/database.db
```

## Advanced Usage

### Dynamic Tool Loading

Load tools based on runtime requirements:

```python
async def create_specialized_agent(task_type: str) -> Agent:
    """Create agent with tools appropriate for the task."""
    mcp = MCP()
    
    if task_type == "web_research":
        await mcp.start_servers(["web-search", "browser"])
        tools = await mcp.get_tools(preset="researcher")
        return Agent("Researcher", "Web research expert", tools=tools)
    
    elif task_type == "code_review":
        await mcp.start_servers(["filesystem", "github"])
        tools = await mcp.get_tools(preset="coder")
        return Agent("Reviewer", "Code review expert", tools=tools)
```

### Tool Composition

Combine tools from multiple sources:

```python
# Get tools from different servers
file_tools = await mcp.get_tools(
    tools=["file_read", "file_write"],
    servers=["filesystem"]
)

github_tools = await mcp.get_tools(
    tools=["create_issue", "create_pr"],
    servers=["github"]  
)

search_tools = await mcp.get_tools(servers=["web-search"])

# Combine for a full-featured agent
all_tools = file_tools + github_tools + search_tools
agent = Agent("Full-Stack Dev", "...", tools=all_tools)
```

### Response Processing

The MCP adapter automatically processes common response formats:

```python
# JSON responses are parsed
"{\"status\": \"ok\", \"count\": 5}"  → {"status": "ok", "count": 5}

# Numbered lists are structured
"1. First\n2. Second"  → {"type": "list", "items": [...]}

# Key-value pairs are extracted
"Name: John\nAge: 30"  → {"type": "key_value", "data": {"name": "John", "age": "30"}}

# Plain text is wrapped
"Hello world"  → {"type": "text", "content": "Hello world"}
```

### Multi-Agent Systems with MCP

```python
from konseho import Council, Agent, DebateStep, ParallelStep
from konseho.mcp import MCP

async def create_development_council():
    """Create a council for software development tasks."""
    # Initialize MCP
    mcp = MCP()
    
    # Start required servers
    await mcp.start_servers(["filesystem", "github", "web-search"])
    
    # Create specialized agents
    architect = Agent(
        "Software Architect",
        "You design system architecture",
        tools=await mcp.get_tools(tools=["file_read", "web_search"])
    )
    
    developer = Agent(
        "Developer", 
        "You implement features",
        tools=await mcp.get_tools(preset="coder")
    )
    
    reviewer = Agent(
        "Code Reviewer",
        "You ensure code quality",
        tools=await mcp.get_tools(
            tools=["file_read", "create_issue"],
            servers=["filesystem", "github"]
        )
    )
    
    # Create council
    council = Council(
        agents=[architect, developer, reviewer],
        steps=[
            DebateStep(
                "Design the solution approach",
                participants=["Software Architect", "Developer"]
            ),
            ParallelStep({
                "Developer": "Implement the solution",
                "Code Reviewer": "Prepare review checklist"
            })
        ]
    )
    
    return council, mcp
```

## Best Practices

### 1. Server Lifecycle Management

Always clean up servers when done:

```python
mcp = MCP()
try:
    await mcp.start_servers(["filesystem", "github"])
    # ... use tools ...
finally:
    await mcp.stop_all_servers()
```

### 2. Error Handling

Handle server startup failures gracefully:

```python
results = await mcp.start_servers(["filesystem", "github", "invalid"])
for server, success in results.items():
    if not success:
        print(f"Failed to start {server}")
```

### 3. Tool Validation

Verify tools are available before use:

```python
tools = await mcp.get_tools(tools=["file_read", "file_write"])
if len(tools) < 2:
    print("Warning: Not all requested tools available")
```

### 4. Performance Considerations

- Start only needed servers
- Cache MCP instance across agents
- Use parallel execution when possible
- Consider server resource limits

### 5. Security

- Review MCP server permissions before use
- Use environment variables for sensitive data
- Limit tool access based on agent purpose
- Configure path restrictions for filesystem access

## Troubleshooting

### Server Won't Start

1. Check server is installed: `npm list -g @modelcontextprotocol/server-name`
2. Verify command in mcp.json is correct
3. Check environment variables are set
4. Look for error messages in console output

### Tools Not Available

1. Ensure server started successfully
2. Check server provides expected tools
3. Verify tool names match exactly
4. Try listing all tools: `await mcp.get_tools()`

### Performance Issues

1. Start only needed servers
2. Cache MCP instance across agents
3. Use connection pooling for database servers
4. Consider server resource limits

## Creating Personas with MCP Tools

```python
from konseho import PersonaTemplate, PersonaRegistry
from konseho.mcp import MCP

# Initialize MCP
mcp = MCP()

# Register personas with MCP tools
registry = PersonaRegistry()

# Software Engineer
await mcp.start_servers(["filesystem", "github"])
engineer_tools = await mcp.get_tools(preset="coder")
registry.register(PersonaTemplate(
    name="Software Engineer",
    instructions="You write clean, tested code",
    tools=engineer_tools
))

# Data Scientist  
await mcp.start_servers(["python-repl", "filesystem"])
scientist_tools = await mcp.get_tools(
    tools=["python_execute", "file_read", "file_write"],
    tags=["data", "analysis"]
)
registry.register(PersonaTemplate(
    name="Data Scientist",
    instructions="You analyze data and create visualizations",
    tools=scientist_tools
))

# Create agents from personas
engineer = registry.create_agent("Software Engineer")
scientist = registry.create_agent("Data Scientist")
```

## Environment Variables

Use `${VAR_NAME}` syntax in mcp.json for environment variables:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Examples

See comprehensive examples in:
- `/examples/mcp_configuration.py` - Configuration and runtime tool selection
- `/examples/mcp_tools_example.py` - Tool wrapping and processing

## Summary

Konseho's MCP integration provides:

1. **Configuration Compatibility**: Use the same mcp.json format as Cline/Claude Code
2. **Runtime Tool Selection**: Choose tools dynamically based on agent needs
3. **Tool Presets**: Pre-configured tool sets for common personas
4. **Automatic Processing**: String responses converted to structured data
5. **Server Management**: Full lifecycle control of MCP servers
6. **Flexible Filtering**: Select tools by name, server, tags, or custom logic

This allows Konseho councils to leverage the entire MCP ecosystem with maximum flexibility and compatibility.