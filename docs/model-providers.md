# Model Provider Setup Guide

Konseho supports multiple LLM providers through the Strands SDK. This guide shows how to configure different providers.

## Quick Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys:**
   ```bash
   # Choose your provider and add the corresponding API key
   DEFAULT_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your-api-key-here
   ```

3. **Install the provider (if needed):**
   ```bash
   # For Anthropic
   pip install strands-agents[anthropic]
   
   # For OpenAI
   pip install strands-agents[openai]
   
   # For all providers
   pip install strands-agents[all]
   ```

## Supported Providers

### 1. Anthropic (Claude)

```bash
# In .env
DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_MODEL=claude-3-opus-20240229
```

Available models:
- `claude-3-opus-20240229` (most capable)
- `claude-3-sonnet-20240229` (balanced)
- `claude-3-haiku-20240307` (fastest)

### 2. OpenAI

```bash
# In .env
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
DEFAULT_MODEL=gpt-4
```

Available models:
- `gpt-4` (most capable)
- `gpt-4-turbo-preview` (faster, cheaper)
- `gpt-3.5-turbo` (fastest, cheapest)

### 3. AWS Bedrock

```bash
# In .env
DEFAULT_PROVIDER=bedrock
DEFAULT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
AWS_DEFAULT_REGION=us-east-1
```

Notes:
- Uses AWS credentials from environment or ~/.aws/credentials
- No API key needed if AWS is configured
- Model IDs follow Bedrock format

### 4. Ollama (Local Models)

```bash
# In .env
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=llama2
OLLAMA_HOST=http://localhost:11434
```

First, install and start Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Start Ollama server (if not running)
ollama serve
```

## Programmatic Configuration

You can also configure models in code:

```python
from konseho.config import ModelConfig, create_model_from_config
from konseho.agents import AgentWrapper
from strands import Agent

# Option 1: Use environment configuration
model = create_model_from_config()
agent = Agent(name="MyAgent", model=model)

# Option 2: Specify configuration
config = ModelConfig(
    provider="anthropic",
    model_id="claude-3-opus-20240229",
    api_key="your-api-key"
)
model = create_model_from_config(config)
agent = Agent(name="MyAgent", model=model)

# Option 3: Direct Strands configuration
from strands.models.anthropic import AnthropicModel
model = AnthropicModel(
    client_args={"api_key": "your-api-key"},
    model_id="claude-3-opus-20240229"
)
agent = Agent(name="MyAgent", model=model)
```

## Per-Agent Configuration

Different agents can use different models:

```python
from konseho import Council, DebateStep
from konseho.agents import AgentWrapper
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.models.anthropic import AnthropicModel

# Fast agent for exploration
explorer_model = OpenAIModel(
    client_args={"api_key": "..."},
    model_id="gpt-3.5-turbo"
)
explorer = AgentWrapper(Agent(name="Explorer", model=explorer_model))

# Powerful agent for planning
planner_model = AnthropicModel(
    client_args={"api_key": "..."},
    model_id="claude-3-opus-20240229"
)
planner = AgentWrapper(Agent(name="Planner", model=planner_model))

# Create council with mixed models
council = Council([
    DebateStep([explorer, planner])
])
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DEFAULT_PROVIDER` | Model provider to use | `anthropic`, `openai`, `bedrock`, `ollama` |
| `DEFAULT_MODEL` | Model ID for the provider | `claude-3-opus-20240229` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `AWS_ACCESS_KEY_ID` | AWS access key (for Bedrock) | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `...` |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `TEMPERATURE` | Model temperature (0-1) | `0.7` |
| `MAX_TOKENS` | Maximum response tokens | `2000` |

## Checking Your Configuration

Run this to verify your setup:

```python
from konseho.config import print_config_info
print_config_info()
```

Output:
```
Provider: anthropic
Model: claude-3-opus-20240229
API Key: Set
Additional args: {'temperature': 0.7, 'max_tokens': 2000}
```

## Troubleshooting

### "Provider not installed" Error
Install the required provider:
```bash
pip install strands-agents[anthropic]  # or [openai], [all]
```

### "API key not set" Error
Make sure your `.env` file contains the API key and is in the project root.

### AWS Bedrock Access Denied
Ensure your AWS credentials have access to Bedrock and the specific model.

### Ollama Connection Refused
Start the Ollama server:
```bash
ollama serve
```