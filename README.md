# Konseho 🏛️

A Python SDK for creating multi-agent "councils" built on top of the [Strands Agent SDK](https://github.com/strands-ai/strands-agents). Konseho enables specialized AI agents to work together through debate, parallel execution, and coordinated workflows to accomplish complex tasks with better context management.

## Features

- **🤝 Multi-Agent Orchestration**: Coordinate multiple specialized agents working together
- **💭 Debate & Consensus**: Agents can propose, debate, and vote on solutions
- **⚡ Parallel Execution**: Run agents concurrently for faster results
- **🔀 Dynamic Work Distribution**: Automatically split tasks across multiple agent instances
- **🧠 Context Management**: Maintain shared memory and state across agent interactions
- **👥 Human-in-the-Loop**: Seamlessly integrate human decision-makers into councils
- **📊 Real-time Monitoring**: Stream events and progress updates as councils execute
- **🛡️ Error Resilience**: Configurable error handling strategies (halt, continue, retry, fallback)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/konseho.git
cd konseho

# Set up development environment (recommended)
./setup-dev.sh

# Or install directly with uv
uv pip install -e .

# Install with specific provider support
uv pip install -e ".[anthropic]"  # For Claude
uv pip install -e ".[openai]"     # For GPT
uv pip install -e ".[dev]"        # For development
```

## Model Provider Setup

### Quick Setup (Recommended)

Run the interactive setup wizard:

```bash
uv run python -m konseho.setup_wizard
```

This will:
- Guide you through provider selection
- Help you configure API keys
- Create a `.env` file
- Check if required packages are installed

### Manual Setup

1. **Create your configuration:**
   ```bash
   # Create .env file in project root
   touch .env
   ```

2. **Add your provider configuration:**
   ```bash
   # For Anthropic (Claude)
   DEFAULT_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your-api-key-here
   DEFAULT_MODEL=claude-3-opus-20240229
   
   # For OpenAI (GPT)
   DEFAULT_PROVIDER=openai
   OPENAI_API_KEY=your-api-key-here
   DEFAULT_MODEL=gpt-4
   
   # For AWS Bedrock
   DEFAULT_PROVIDER=bedrock
   DEFAULT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
   AWS_DEFAULT_REGION=us-east-1
   
   # For Ollama (Local)
   DEFAULT_PROVIDER=ollama
   DEFAULT_MODEL=llama2
   OLLAMA_HOST=http://localhost:11434
   ```

3. **Verify configuration:**
   ```bash
   uv run python -m konseho --config
   ```

Supported providers:
- **Anthropic** (Claude): Get API key at https://console.anthropic.com/settings/keys
- **OpenAI** (GPT): Get API key at https://platform.openai.com/api-keys
- **AWS Bedrock**: Uses AWS credentials (configure AWS CLI)
- **Ollama**: Local models, requires Ollama server running

See [Model Providers Guide](docs/model-providers.md) for detailed setup.

## Interactive Chat Interface

Start the interactive chat interface:

```bash
# Run with example agents
uv run python -m konseho

# Or run the chat demo
uv run python examples/chat_demo.py

# Show help
uv run python -m konseho --help
```

The chat interface provides:
- 🎯 Real-time event display as agents work
- 💬 Interactive task input
- 📊 Formatted results display
- 🔄 Continuous session support

## Quick Start

Create a simple council in less than 10 lines of code:

```python
from konseho import Council, DebateStep
from konseho.agents import AgentWrapper
from strands import Agent
from konseho.config import create_model_from_config

# Create model (uses your .env configuration)
model = create_model_from_config()

# Create specialized agents
explorer = AgentWrapper(Agent("Explorer", model=model))
planner = AgentWrapper(Agent("Planner", model=model))
coder = AgentWrapper(Agent("Coder", model=model))

# Create a council with a debate step
council = Council([
    DebateStep([explorer, planner, coder])
])

# Execute the council
result = council.run("Fix the authentication bug in login.py")
```

## Core Concepts

### 1. Council
The main orchestrator that manages multiple agents working together through defined steps.

```python
council = Council(
    name="MyCouncil",
    steps=[...],           # List of execution steps
    error_strategy="halt"  # How to handle errors
)
```

### 2. Steps
Different execution patterns for agent coordination:

#### DebateStep
Agents propose competing solutions and vote on the best one.

```python
DebateStep(
    agents=[agent1, agent2, agent3],
    rounds=2,                    # Number of debate rounds
    voting_strategy="majority"   # majority, consensus, weighted, moderator
)
```

#### ParallelStep
Agents work on different aspects simultaneously.

```python
ParallelStep(
    agents=[frontend_dev, backend_dev, db_expert],
    task_splitter=custom_splitter  # Optional function to split tasks
)
```

#### SplitStep
Dynamically distributes work across multiple agent instances.

```python
SplitStep(
    agent_template=base_agent,
    min_agents=2,
    max_agents=10,
    split_strategy="auto"  # auto, fixed, adaptive
)
```

### 3. Context Management
Shared memory and state that flows between agents and steps.

```python
context = Context(initial_data={"project": "MyApp"})
context.add("findings", exploration_results)
context.get_summary()  # Get full context state
```

## Examples

All examples are in the `examples/` directory. To run any example:

```bash
# Make sure you've configured your model provider first
uv run python -m konseho.setup_wizard

# Run an example
uv run python examples/simple_council.py
```

### Available Examples

1. **simple_council.py** - Basic debate council with 2 agents
2. **simple_council_mock.py** - Mock version for testing without API keys
3. **research_council.py** - Multi-step council for research tasks
4. **code_review_council.py** - Parallel code review by multiple agents
5. **human_in_loop_council.py** - Council with human participation
6. **chat_demo.py** - Interactive chat interface demonstration
7. **setup_and_run.py** - Diagnostic tool to verify configuration

### Code Review Council

```python
from konseho import Council, ParallelStep, DebateStep
from konseho.agents import AgentWrapper
from examples.agents import ExplorerAgent, ReviewerAgent, CoderAgent

# Create specialized agents
explorer = AgentWrapper(ExplorerAgent())
reviewer1 = AgentWrapper(ReviewerAgent(name="Security"))
reviewer2 = AgentWrapper(ReviewerAgent(name="Performance"))
coder = AgentWrapper(CoderAgent())

# Multi-step review process
council = Council([
    # Step 1: Explore and review in parallel
    ParallelStep([explorer, reviewer1]),
    
    # Step 2: Debate on findings
    DebateStep([reviewer1, reviewer2], voting_strategy="consensus"),
    
    # Step 3: Implement improvements
    ParallelStep([coder])
])

result = council.run("Review authentication module for security issues")
```

### Research Council with Dynamic Splitting

```python
from konseho import Council, SplitStep, DebateStep

# Research council that scales based on task complexity
council = Council([
    # Dynamically split research across agents
    SplitStep(
        agent_template=ResearchAgent(),
        split_strategy="auto"  # Automatically determine agent count
    ),
    
    # Synthesize findings
    DebateStep([Synthesizer1(), Synthesizer2()])
])

result = council.run("""
Research distributed caching strategies including:
- Caching algorithms (LRU, LFU, FIFO)
- Distributed solutions (Redis, Hazelcast)
- Consistency models
- Partitioning strategies
""")
```

### Human-in-the-Loop Council

```python
from konseho import Council, DebateStep
from konseho.agents import HumanAgent, AgentWrapper

# Include human decision-maker
human = AgentWrapper(HumanAgent(name="ProductOwner"))
ai_planner = AgentWrapper(PlannerAgent())
ai_developer = AgentWrapper(DeveloperAgent())

council = Council([
    DebateStep(
        agents=[human, ai_planner, ai_developer],
        moderator=human,  # Human has final say
        voting_strategy="moderator"
    )
])

result = council.run("Design user notification system")
```

## Advanced Features

### Voting Strategies

- **Majority**: Most votes wins
- **Consensus**: All agents must agree (with configurable rounds)
- **Weighted**: Votes weighted by agent expertise
- **Moderator**: Designated agent makes final decision

### Error Handling Strategies

- **halt**: Stop execution on first error (default)
- **continue**: Log error and proceed to next step
- **retry**: Retry failed step once
- **fallback**: Use fallback result and continue

### Event Streaming

```python
async for event in council.stream_execute(task):
    print(f"{event.type}: {event.data}")
    # Outputs:
    # council:start: {"council": "MyCouncil", "task": "..."}
    # step:start: {"step": 0, "type": "DebateStep"}
    # agent:working: {"agent": "Explorer", "task": "..."}
    # ...
```

## Creating Custom Agents

Extend the base agents or create your own:

```python
from strands import Agent

class DataAnalyst(Agent):
    def __init__(self):
        super().__init__(
            name="DataAnalyst",
            model="gpt-4",
            tools=["read_csv", "analyze", "visualize"],
            system_prompt="You are a data analysis expert..."
        )
```

## Architecture

```
konseho/
├── core/           # Council, Steps, Context management
│   ├── council.py  # Main Council orchestrator
│   ├── steps.py    # DebateStep, ParallelStep, SplitStep
│   └── context.py  # Shared context management
├── agents/         # Agent wrappers and human integration
│   ├── base.py     # AgentWrapper for Strands compatibility
│   └── human.py    # HumanAgent for human-in-the-loop
├── execution/      # Async execution engine and events
│   ├── executor.py # Async task execution
│   └── events.py   # Event system for real-time updates
├── interface/      # Terminal chat interface
│   └── chat.py     # Interactive CLI interface
├── config.py       # Model provider configuration
├── setup_wizard.py # First-run setup helper
└── main.py         # Entry point for CLI
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/konseho.git
cd konseho

# Set up development environment
./setup-dev.sh

# Run the project
./run.sh
# Or directly:
uv run python -m konseho

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_main.py::test_specific

# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src

# Run all quality checks
uv run black src tests && uv run ruff check src tests && uv run mypy src && uv run pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built on top of the excellent [Strands Agents SDK](https://github.com/strands-ai/strands-agents). The name "Konseho" comes from the Tagalog word for "council," reflecting the collaborative nature of agent interactions.