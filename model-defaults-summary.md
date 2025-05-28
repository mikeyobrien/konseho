# Model Defaults Configuration Summary

## Changes Made

### 1. Query Analyzer - Uses Claude Sonnet 4
- **File**: `src/konseho/dynamic/model_analyzer.py`
- **Changes**:
  - `ModelBasedAnalyzer.__init__`: Now defaults to `"claude-sonnet-4-20250514"` if no model is specified
  - `ModelAnalyzer.__init__`: Explicitly sets default to Claude Sonnet 4 before passing to `ModelBasedAnalyzer`

### 2. Persona Agents - Use Claude 3.5 Haiku
- **File**: `src/konseho/dynamic/model_agent_factory.py`
- **Changes**:
  - `ModelAgentFactory.create_agents_from_spec`: Now passes `model="claude-3-5-haiku-20241022"` when creating agents from personas

### 3. Documentation Updates
- **File**: `src/konseho/dynamic/builder.py`
- **Changes**:
  - Updated docstrings to reflect that the analyzer defaults to Claude Sonnet 4

## How It Works

1. **Query Analysis Phase**: When a dynamic council is created, the query is analyzed using Claude Sonnet 4 to determine:
   - Task type and complexity
   - Required agent personas
   - Optimal workflow steps

2. **Agent Creation Phase**: Based on the analysis, persona agents are created using Claude 3.5 Haiku:
   - Each persona (Security Expert, Code Architect, etc.) uses Claude 3.5 Haiku for faster, cost-effective execution
   - Agents work in parallel or debate modes as determined by the analyzer

## Benefits

- **Better Analysis**: Claude Sonnet 4 provides sophisticated query understanding and council planning
- **Cost Efficiency**: Claude 3.5 Haiku for actual agent work reduces costs while maintaining quality
- **Performance**: Haiku's faster response times improve overall council execution speed

## Usage

No changes needed in how you use Konseho. The defaults are applied automatically:

```python
# This will use Claude Sonnet 4 for analysis, Claude 3.5 Haiku for agents
council = await create_dynamic_council("Review this code for security issues")
result = await council.run(code_to_review)
```

To override defaults:

```python
# Use a different analyzer model
council = await create_dynamic_council(
    "Your query", 
    analyzer_model="claude-3-opus-20240229"
)

# For custom agents, specify model explicitly
agent = create_agent(
    name="CustomAgent",
    system_prompt="...",
    model="claude-3-5-sonnet-20241022"  # Override default
)
```