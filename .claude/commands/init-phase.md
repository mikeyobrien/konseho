# Initialize Project Phase

Set up the Konseho project structure and dependencies according to the implementation plan.

## Important: Research Strands First
Before setting up the project, use the Strands MCP server if available:

### If you have Strands MCP server configured:
```
mcp_strands_agents_mcp_server:quickstart
mcp_strands_agents_mcp_server:model_providers
mcp_strands_agents_mcp_server:agent_tools
```

### Otherwise, research manually:
1. Search for the Strands Agents SDK on GitHub/PyPI
2. The package name is "strands-agents"
3. Review documentation at: https://github.com/strands-agents
4. Note version requirements and dependencies
5. Understand the basic API structure

Key concepts to understand:
- How to create an Agent
- How to add tools with @tool decorator
- Message format and conversation management
- Model provider configuration

## Tasks:
1. Create the package structure:
   - konseho/core/ (council.py, steps.py, context.py)
   - konseho/agents/ (base.py, human.py)
   - konseho/execution/ (executor.py, events.py)
   - konseho/interface/ (chat.py)

2. Update pyproject.toml with all required dependencies:
   - strands-agents (main dependency)
   - asyncio, typing-extensions
   - rich (for terminal output)
   - pydantic (for config validation)

3. Create initial __init__.py files with proper exports

4. Set up basic logging configuration

5. Create examples/ and tests/ directories

Remember: The goal is <10 lines of code to create a functional council!

## Initial Commit
After setting up the project structure:

```bash
# Initialize git repository if not already done
git init

# Add initial files
git add .
git commit -m "chore: initialize Konseho project structure

- Set up Python package structure
- Configure development dependencies
- Add testing and linting setup
- Include basic documentation
- Follow implementation plan from docs/"
```

**Note**: Keep the initial setup minimal - we'll add features incrementally following TDD.