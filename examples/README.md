# Konseho Examples

This directory contains examples showing how to use Konseho councils.

## Running Examples

### Prerequisites

Konseho requires a configured model provider (Anthropic, OpenAI, or AWS Bedrock). Without credentials, you'll see agents returning immediately without meaningful output.

To configure:
```bash
# Option 1: Run the setup wizard
konseho setup

# Option 2: Set environment variables
export ANTHROPIC_API_KEY=your_key  # For Anthropic
# OR
export OPENAI_API_KEY=your_key     # For OpenAI
# OR
export AWS_ACCESS_KEY_ID=your_key  # For AWS Bedrock
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### Available Examples

1. **simple_council.py** - Basic debate council with 2 agents
2. **research_council.py** - Multi-step council for research tasks
3. **code_review_council.py** - Parallel code review by multiple agents
4. **human_in_loop_council.py** - Council with human participation
5. **chat_demo.py** - Interactive chat interface demonstration
6. **custom_analyzer_model.py** - Using different models for query analysis
7. **real_search.py** - Using real search providers (Brave, Tavily, etc.)
8. **search_provider_demo.py** - Comprehensive search provider integration demo
9. **mcp_search_example.py** - Using MCP search servers with Konseho
10. **mcp_tools_example.py** - General MCP tool integration

### Running an Example

```bash
# With uv (recommended)
uv run python examples/simple_council.py

# Or with regular Python
python examples/simple_council.py
```

### Mock Examples (No API Required)

For testing without API credentials:

1. **simple_council_mock.py** - Uses mock agents that don't require API keys
   ```bash
   uv run python examples/simple_council_mock.py
   ```

Note: Mock agents return fixed responses and don't implement the full debate/voting protocol, so results won't be as meaningful as with real AI agents.

### Understanding the Output

When running with mock agents, you might see:
- Immediate responses without actual AI processing
- Zero votes (mock agents don't implement voting protocol)
- Repeated identical responses

This is expected behavior with mocks. For real AI-powered debates and collaboration, configure a model provider.

### Troubleshooting

If you see "Council Result" with empty or zero votes:
1. Check that your API credentials are configured
2. Verify you have network access to the model provider
3. Ensure you're using the correct model ID for your provider

Run `examples/setup_and_run.py` for a diagnostic check of your configuration.

### Dynamic Councils with Custom Analyzer Models

The dynamic council builder uses AI to analyze your query and automatically create the right agents and workflow. You can customize which model is used for this analysis:

```python
# Use a fast model for query analysis
builder = DynamicCouncilBuilder(
    analyzer_model="claude-3-haiku-20240307",
    analyzer_temperature=0.3
)

# Or use a more capable model for complex queries
builder = DynamicCouncilBuilder(
    analyzer_model="claude-3-5-sonnet-20241022"
)
```

From the command line:
```bash
# Specify analyzer model for dynamic councils
konseho --dynamic --analyzer-model claude-3-haiku-20240307
```

Note: Model-based analysis is now required for dynamic councils. There is no fallback to heuristic analysis.

## Web Search Integration

Konseho agents can use web search through custom search providers. By default, a mock search provider is used for testing and demos.

### Using Real Search Providers

To use real web search (Brave, Tavily, etc.), you need to:

1. **Get an API key** from your chosen provider:
   - Brave Search: https://brave.com/search/api
   - Tavily: https://tavily.com
   - Serper (Google): https://serper.dev

2. **Set your API key**:
   ```bash
   export BRAVE_API_KEY="your-api-key-here"
   # or
   export TAVILY_API_KEY="your-api-key-here"
   ```

3. **Run the example**:
   ```bash
   uv run python examples/real_search.py
   ```

The example shows how to:
- Implement custom SearchProvider classes
- Configure search providers globally
- Use search in multi-agent councils

### Search Provider Options

Konseho supports multiple ways to integrate search:

1. **Mock/Fake Providers** - For testing without API keys
   - `MockSearchProvider` - General purpose testing
   - Custom fake providers - Domain-specific testing

2. **MCP Search Servers** - If you have MCP servers configured
   - Use `MCPSearchProvider` to wrap MCP search tools
   - Works with brave-search, tavily, and other MCP servers
   - See `mcp_search_example.py` for details

3. **Direct API Integration** - Using search APIs directly
   - Implement custom `SearchProvider` classes
   - Examples: Brave, Tavily, Serper, etc.
   - See `real_search.py` for implementation

4. **Configuration-Based** - Dynamic provider selection
   - Use environment variables (`SEARCH_PROVIDER`)
   - Different providers for different agents
   - See `search_provider_demo.py` for comprehensive examples

### Important Note on MCP

While Konseho agents cannot directly access MCP tools (since they run via API calls, not locally), the MCP integration allows you to:
- Use MCP servers configured in `mcp.json`
- Wrap MCP tools for use by agents
- Leverage the same search servers used by Cline/Claude Code