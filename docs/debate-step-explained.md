# How the DebateStep Works

The DebateStep is one of the core coordination patterns in Konseho that enables multiple agents to propose competing solutions, critique each other's ideas, and reach a consensus through voting.

## Overview

The DebateStep implements a structured debate process where:
1. Agents propose initial solutions
2. They engage in multiple rounds of critique and refinement
3. A winner is selected through various voting strategies

## Key Components

### Initialization Parameters

```python
DebateStep(
    agents: List[AgentWrapper],      # Participating agents
    moderator: Optional[AgentWrapper] = None,  # Optional moderator
    rounds: int = 2,                 # Number of debate rounds
    voting_strategy: str = "majority"  # How to determine winner
)
```

### Voting Strategies

1. **"majority"** - Simple majority vote wins
2. **"weighted"** - Votes weighted by agent expertise level
3. **"consensus"** - Attempts to reach unanimous agreement
4. **"moderator"** - Moderator selects the winner

## Step-by-Step Process

### 1. Initial Proposals Phase

```python
# Each agent receives the task and context
prompt = f"{task}\n\n{context.to_prompt_context()}"

# All agents work in parallel to create initial proposals
initial_proposals = await asyncio.gather(*proposal_tasks)

# Store proposals by agent name
proposals["Agent1"] = "Agent1's solution..."
proposals["Agent2"] = "Agent2's solution..."
```

### 2. Debate Rounds

For each debate round:

```python
# Create debate context showing all proposals so far
debate_context = f"Debate Round {round_num + 1}\n\nCurrent Proposals:\n"
# Include summaries of all proposals (truncated to 500 chars)

# Each agent sees others' proposals and can:
# - Critique other proposals
# - Defend their own approach
# - Modify their proposal based on feedback
# - Build on others' ideas

# New proposals are stored with round number
proposals[f"{agent.name}_round_{round_num}"] = updated_proposal
```

### 3. Consensus Check (Optional)

If using consensus strategy, after each round:
```python
# Check if all agents converged on similar solution
if all proposals are very similar (first 100 chars match):
    consensus_reached = True
    break  # End debate early
```

### 4. Voting Phase

After debate rounds complete, agents vote:

```python
# Create voting prompt with all original proposals
voting_prompt = """
Vote for the best proposal. Reply with 'I vote for: [agent name]' 
or 'I abstain from voting'

Agent1: [proposal summary]...
Agent2: [proposal summary]...
"""

# Collect votes in parallel
vote_responses = await asyncio.gather(*vote_tasks)

# Extract votes using pattern matching
# Looks for "I vote for: AgentName" in responses
```

### 5. Vote Counting

Different strategies count votes differently:

#### Majority Voting
```python
# Count raw votes for each proposal
vote_counts = {"proposal1": 3, "proposal2": 2}

# Handle ties by selecting first proposal
if tie:
    winner = first_proposal_with_max_votes
```

#### Weighted Voting
```python
# Each agent's vote weighted by expertise_level (0.0-1.0)
weighted_scores["proposal1"] = 0.9 + 0.7 + 0.8  # 2.4
weighted_scores["proposal2"] = 0.6 + 0.5       # 1.1

winner = proposal_with_highest_weighted_score
```

#### Moderator Selection
```python
# Moderator sees all proposals and selects winner
moderator_prompt = "Select the best proposal for: {task}"
# Extract moderator's choice from response
```

### 6. Result Structure

The DebateStep returns:
```python
{
    "winner": "The selected winning proposal text",
    "proposals": {
        "Agent1": "Initial proposal...",
        "Agent1_round_0": "Round 1 update...",
        "Agent2": "Initial proposal...",
        # ... all proposals from all rounds
    },
    "strategy": "majority",
    "votes": {"Agent1": 2, "Agent2": 1},  # Vote counts
    "abstentions": 1,                      # Number who abstained
    "total_votes": 3,
    # Additional fields based on strategy...
}
```

## Example Flow

Here's a concrete example with 3 agents debating how to implement a feature:

```python
# Round 0: Initial Proposals
Agent1: "We should use React with TypeScript..."
Agent2: "I propose a Vue.js solution..."  
Agent3: "Consider using vanilla JavaScript..."

# Round 1: Critique and Refinement
Agent1: "While Vue.js has merits, React's ecosystem..."
Agent2: "I see the TypeScript benefits. Updated proposal..."
Agent3: "Both frameworks are overkill. Here's why..."

# Round 2: Final Arguments
Agent1: "Incorporating feedback, React + TypeScript + testing..."
Agent2: "Agreed on TypeScript. Vue + TypeScript compromise..."
Agent3: "Progressive enhancement with vanilla JS first..."

# Voting
Agent1: "I vote for: Agent1"  # (Can vote for self)
Agent2: "I vote for: Agent1"  # (Convinced by arguments)
Agent3: "I vote for: Agent3"  # (Sticks to position)

# Result
Winner: Agent1's proposal (2 votes vs 1)
```

## Best Practices

### 1. Agent Specialization
Give agents different perspectives:
```python
security_expert = AgentWrapper(
    create_agent(system_prompt="Focus on security implications..."),
    name="SecurityExpert",
    expertise_level=0.9  # High weight for security topics
)

ux_designer = AgentWrapper(
    create_agent(system_prompt="Prioritize user experience..."),
    name="UXDesigner", 
    expertise_level=0.8
)
```

### 2. Context Management
Provide rich context for informed debate:
```python
context = Context()
context.add("requirements", detailed_requirements)
context.add("constraints", technical_constraints)
context.add("previous_decisions", architectural_decisions)
```

### 3. Optimal Round Count
- **1 round**: Quick decisions, less refinement
- **2-3 rounds**: Good balance of depth and efficiency
- **4+ rounds**: Deep exploration but diminishing returns

### 4. Voting Strategy Selection
- **Majority**: Democratic, good for equally skilled agents
- **Weighted**: When some agents have more relevant expertise
- **Consensus**: When agreement is crucial (e.g., architecture decisions)
- **Moderator**: When you need human oversight or tiebreaking

## Common Patterns

### 1. Architecture Review Council
```python
council = Council(
    name="ArchitectureReview",
    steps=[
        DebateStep(
            agents=[architect, security_expert, devops_engineer],
            rounds=3,
            voting_strategy="consensus"  # All must agree
        )
    ]
)
```

### 2. Feature Planning Council
```python
council = Council(
    name="FeaturePlanning",
    steps=[
        DebateStep(
            agents=[product_manager, tech_lead, ux_designer],
            moderator=human_agent,  # Human makes final call
            rounds=2,
            voting_strategy="moderator"
        )
    ]
)
```

### 3. Code Review Council
```python
council = Council(
    name="CodeReview",
    steps=[
        DebateStep(
            agents=[senior_dev, security_auditor, performance_expert],
            rounds=1,  # Quick review
            voting_strategy="weighted"  # Expertise matters
        )
    ]
)
```

## Implementation Details

### Vote Extraction
The system uses regex patterns to extract votes:
```python
# Looks for pattern: "I vote for: [name]"
vote_match = re.search(r"I vote for:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)

# Also checks for abstention
if "abstain" in response.lower():
    return "ABSTAIN"
```

### Proposal Truncation
To keep debate prompts manageable:
- Initial proposals shown as first 500 characters
- Voting summaries show first 200 characters
- Full proposals are preserved in results

### Error Handling
- If no votes cast, first proposal wins
- If all abstain, first proposal wins  
- If tie, first tied proposal wins
- If moderator unclear, first proposal wins

## Tips for Effective Debates

1. **Clear Task Definition**: Be specific about what you're asking
2. **Diverse Perspectives**: Use agents with different backgrounds
3. **Structured Prompts**: Guide agents on how to structure proposals
4. **Iterative Refinement**: Use multiple rounds for complex decisions
5. **Post-Processing**: The winner can be further refined by subsequent steps

## Debugging Debates

Enable verbose output to see the debate flow:
```python
# The result includes all proposals from all rounds
result = await debate_step.execute(task, context)

# Examine the debate progression
for key, proposal in result['proposals'].items():
    print(f"{key}: {proposal[:100]}...")

# Check voting patterns
print(f"Votes: {result.get('votes', {})}")
print(f"Winner: {result['winner'][:200]}...")
```

This structured debate process ensures that multiple perspectives are considered, ideas are refined through critique, and the best solution emerges through a democratic or expertise-weighted process.