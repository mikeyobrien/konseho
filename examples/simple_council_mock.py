"""Simple example using mock agents for testing without credentials."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from konseho import Council, DebateStep, AgentWrapper
from tests.fixtures.mock_agents import MockStrandsAgent

# Create mock agents that don't require API credentials
agent1 = MockStrandsAgent("Alice", "Python is best for beginners due to its simplicity")
agent2 = MockStrandsAgent("Bob", "JavaScript is better because of immediate visual feedback")

council = Council(
    name="simple_debate",
    steps=[DebateStep([AgentWrapper(agent1, "Alice"), AgentWrapper(agent2, "Bob")])]
)

# Run the council
print("Running mock council debate...")
result = council.run("What's the best programming language for beginners?")
print(f"\nCouncil Result:\n{result}")