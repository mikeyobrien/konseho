# Konseho Step Types Guide

Konseho provides three main step types for coordinating agent workflows, each designed for different collaboration patterns.

## 1. DebateStep

**Purpose**: Agents propose competing solutions and vote on the best one.

### When to Use
- Making architectural decisions
- Choosing between multiple approaches
- Code review with different perspectives
- When you need democratic consensus

### Key Features
- Multiple rounds of proposal and critique
- Various voting strategies (majority, weighted, consensus, moderator)
- Agents can see and respond to each other's ideas
- Built-in conflict resolution

### Example
```python
from konseho import Council, DebateStep
from konseho.agents.base import AgentWrapper, create_agent

# Create specialized agents
architect = AgentWrapper(
    create_agent(
        name="Architect",
        system_prompt="You focus on system design and scalability.",
        temperature=0.7
    ),
    name="Architect",
    expertise_level=0.9  # High expertise weight
)

security = AgentWrapper(
    create_agent(
        name="SecurityExpert",
        system_prompt="You focus on security best practices.",
        temperature=0.6
    ),
    name="SecurityExpert",
    expertise_level=0.85
)

developer = AgentWrapper(
    create_agent(
        name="Developer",
        system_prompt="You focus on practical implementation.",
        temperature=0.7
    ),
    name="Developer",
    expertise_level=0.8
)

# Create debate step
debate = DebateStep(
    agents=[architect, security, developer],
    rounds=2,  # Two rounds of debate
    voting_strategy="weighted"  # Weight votes by expertise
)

council = Council(
    name="DesignReview",
    steps=[debate]
)

result = await council.execute("Design a user authentication system")
```

### Result Structure
```python
{
    "winner": "The selected winning proposal...",
    "proposals": {
        "Architect": "Initial proposal...",
        "Architect_round_0": "Refined proposal...",
        "SecurityExpert": "Initial proposal...",
        # ... all proposals
    },
    "votes": {"Architect": 2, "SecurityExpert": 1},
    "weighted_scores": {"Architect": 2.5, "SecurityExpert": 0.85},
    "strategy": "weighted"
}
```

## 2. ParallelStep

**Purpose**: Agents work on different aspects simultaneously without interaction.

### When to Use
- Analyzing different facets of a problem
- Gathering diverse perspectives quickly
- When subtasks are independent
- For comprehensive research or analysis

### Key Features
- All agents work concurrently
- Optional task splitter to assign different subtasks
- No interaction between agents
- Maximum efficiency for independent work

### Example
```python
from konseho import Council, ParallelStep

# Create agents with different specialties
frontend_dev = AgentWrapper(
    create_agent(
        name="FrontendDev",
        system_prompt="You analyze frontend and UI aspects.",
    ),
    name="FrontendDev"
)

backend_dev = AgentWrapper(
    create_agent(
        name="BackendDev",
        system_prompt="You analyze backend and API aspects.",
    ),
    name="BackendDev"
)

db_expert = AgentWrapper(
    create_agent(
        name="DatabaseExpert",
        system_prompt="You analyze data storage and retrieval.",
    ),
    name="DatabaseExpert"
)

# Define how to split the task
def split_by_layer(task: str, num_agents: int) -> List[str]:
    base_task = task
    return [
        f"Frontend perspective: {base_task}",
        f"Backend perspective: {base_task}",
        f"Database perspective: {base_task}"
    ]

# Create parallel step
parallel = ParallelStep(
    agents=[frontend_dev, backend_dev, db_expert],
    task_splitter=split_by_layer  # Optional custom splitter
)

council = Council(
    name="SystemAnalysis",
    steps=[parallel]
)

result = await council.execute("Analyze requirements for an e-commerce platform")
```

### Result Structure
```python
{
    "parallel_results": {
        "FrontendDev": "Frontend analysis...",
        "BackendDev": "Backend analysis...",
        "DatabaseExpert": "Database design analysis..."
    },
    "execution_time": "parallel"
}
```

### Without Task Splitter
If you don't provide a task splitter, all agents get the same task:

```python
# All agents work on the same task independently
parallel = ParallelStep(agents=[analyst1, analyst2, analyst3])
```

## 3. SplitStep

**Purpose**: Dynamically create multiple instances of the same agent type to divide work.

### When to Use
- Processing lists or multiple items
- When task naturally splits into similar subtasks
- Scaling analysis based on workload
- Parallel processing with homogeneous agents

### Key Features
- Clones a template agent multiple times
- Intelligent task splitting algorithms
- Adaptive agent count based on task complexity
- Handles various input formats (lists, components, etc.)

### Example
```python
from konseho import Council, SplitStep
from konseho.agents.base import create_agent

# Create a template agent
code_reviewer = create_agent(
    name="CodeReviewer",
    system_prompt="You review code for quality and best practices.",
    temperature=0.6
)

# Create split step
split = SplitStep(
    agent_template=code_reviewer,
    min_agents=2,
    max_agents=5,
    split_strategy="auto"  # Automatically determine agent count
)

council = Council(
    name="CodeReviewTeam",
    steps=[split]
)

# The task will be intelligently split
task = """
Review these files:
1. authentication.py - User login and registration
2. database.py - Database connection and queries  
3. api.py - REST API endpoints
4. utils.py - Helper functions
"""

result = await council.execute(task)
```

### Split Strategies

#### "auto" - Intelligent splitting based on:
- Word count (more text = more agents)
- List detection (numbered/bulleted items)
- Component detection (frontend, backend, etc.)
- File/path patterns

#### "fixed" - Always use minimum agents
```python
split = SplitStep(
    agent_template=analyzer,
    min_agents=3,  # Always use 3 agents
    split_strategy="fixed"
)
```

#### "adaptive" - Custom logic (future feature)

### Result Structure
```python
{
    "split_results": [
        "Review of authentication.py...",
        "Review of database.py...",
        "Review of api.py...",
        "Review of utils.py..."
    ],
    "num_agents": 4,
    "strategy": "auto"
}
```

## Combining Steps

Steps can be combined to create sophisticated workflows:

```python
council = Council(
    name="ComprehensiveReview",
    steps=[
        # First: Parallel analysis from different perspectives
        ParallelStep(agents=[security, performance, ux]),
        
        # Second: Debate the findings
        DebateStep(
            agents=[architect, lead_dev, product_manager],
            rounds=2,
            voting_strategy="consensus"
        ),
        
        # Third: Split implementation tasks
        SplitStep(
            agent_template=developer,
            min_agents=2,
            max_agents=5
        )
    ]
)
```

## Comparison Table

| Feature | DebateStep | ParallelStep | SplitStep |
|---------|------------|--------------|-----------|
| **Agent Interaction** | Yes, through debate | No | No |
| **Best For** | Decision making | Multi-faceted analysis | Workload distribution |
| **Agent Types** | Different specialties | Different perspectives | Same template cloned |
| **Execution** | Sequential rounds | Concurrent | Concurrent |
| **Output** | Single winner | All results | All results |
| **Customization** | Voting strategy | Task splitter | Split strategy |

## Creating Custom Steps

You can create custom steps by inheriting from the Step base class:

```python
from konseho.core.steps import Step
from konseho.core.context import Context

class CustomStep(Step):
    """Your custom coordination pattern."""
    
    def __init__(self, agents, custom_param):
        self.agents = agents
        self.custom_param = custom_param
    
    async def execute(self, task: str, context: Context) -> Dict[str, Any]:
        # Your custom logic here
        results = []
        
        for agent in self.agents:
            # Custom coordination pattern
            result = await agent.work_on(f"{task} with {self.custom_param}")
            results.append(result)
        
        return {
            "custom_results": results,
            "param_used": self.custom_param
        }
```

## Best Practices

### 1. Choose the Right Step
- **DebateStep**: When you need consensus or best solution selection
- **ParallelStep**: When you need comprehensive, multi-angle analysis
- **SplitStep**: When you have divisible workload

### 2. Context Management
Always provide rich context for better results:
```python
context = Context()
context.add("requirements", detailed_requirements)
context.add("constraints", technical_limits)
context.add("previous_work", related_decisions)

council = Council(
    name="InformedCouncil",
    steps=[...],
    context=context
)
```

### 3. Step Parameters
- **DebateStep rounds**: 1-2 for quick decisions, 3-4 for complex topics
- **ParallelStep agents**: 3-5 different perspectives usually sufficient
- **SplitStep max_agents**: Don't over-parallelize, 5-10 is usually the sweet spot

### 4. Result Processing
Each step returns different structures. Plan your result handling:

```python
result = await council.execute(task)

# Access step results
step_results = result.get("results", {})

# For DebateStep
if "step_0" in step_results and "winner" in step_results["step_0"]:
    winning_proposal = step_results["step_0"]["winner"]

# For ParallelStep  
if "step_0" in step_results and "parallel_results" in step_results["step_0"]:
    all_analyses = step_results["step_0"]["parallel_results"]

# For SplitStep
if "step_0" in step_results and "split_results" in step_results["step_0"]:
    all_reviews = step_results["step_0"]["split_results"]
```

These three step types provide flexible building blocks for creating sophisticated multi-agent workflows tailored to your specific needs.