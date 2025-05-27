"""Simple example showing <10 lines council creation."""

from strands import Agent

from konseho import AgentWrapper, Council, DebateStep

# Create agents and council in under 10 lines!
agent1 = Agent(model="us.anthropic.claude-3-5-haiku-20241022-v1:0", tools=[])
agent2 = Agent(model="us.anthropic.claude-3-5-haiku-20241022-v1:0", tools=[])

council = Council(
    name="simple_debate",
    steps=[DebateStep([AgentWrapper(agent1, "Alice"), AgentWrapper(agent2, "Bob")])]
)

# Run the council
result = council.run("What's the best programming language for beginners?")