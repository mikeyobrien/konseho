"""Example showing how to set up model providers and run a council."""

import os

from strands import Agent

from konseho import AgentWrapper, DebateStep
from konseho.factories import CouncilFactory

print("=== Konseho Council Example ===\n")

# Check for configured model providers
if not os.environ.get("AWS_ACCESS_KEY_ID") and not os.environ.get("ANTHROPIC_API_KEY"):
    print("❌ No model providers configured!")
    print("\nTo use Konseho, you need to configure at least one model provider:")
    print("\n1. AWS Bedrock (for Claude models):")
    print("   export AWS_ACCESS_KEY_ID=your_key")
    print("   export AWS_SECRET_ACCESS_KEY=your_secret")
    print("   export AWS_DEFAULT_REGION=us-east-1")
    print("\n2. Anthropic API:")
    print("   export ANTHROPIC_API_KEY=your_api_key")
    print("\n3. OpenAI API:")
    print("   export OPENAI_API_KEY=your_api_key")
    print("\nRun 'konseho setup' for interactive configuration.")
    exit(1)

# Determine which model to use based on available credentials
if os.environ.get("AWS_ACCESS_KEY_ID"):
    # Use Bedrock Claude model
    model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    print(f"✓ Using AWS Bedrock model: {model_id}")
elif os.environ.get("ANTHROPIC_API_KEY"):
    # Use Anthropic API
    model_id = "claude-3-haiku-20240307"
    print(f"✓ Using Anthropic API model: {model_id}")
else:
    # Use OpenAI as fallback
    model_id = "gpt-3.5-turbo"
    print(f"✓ Using OpenAI API model: {model_id}")

# Create agents
print("\nCreating council with 2 agents...")
agent1 = Agent(model=model_id, tools=[])
agent2 = Agent(model=model_id, tools=[])

# Create council with debate step
factory = CouncilFactory()

council = factory.create_council(
    name="example_debate",
    steps=[
        DebateStep(
    agents=[
                AgentWrapper(agent1, "Expert1"),
                AgentWrapper(agent2, "Expert2")
            ],
            rounds=2,
            voting_strategy="majority"
        )
    ]
)

# Run a task
task = "What's the best programming language for beginners?"
print(f"\nRunning council with task: '{task}'")
print("This may take a moment...\n")

try:
    result = council.run(task)
    
    # Display results
    print("=== Council Results ===")
    print(f"\nWinner: {result['results']['step_0']['winner']}")
    print(f"\nVoting Strategy: {result['results']['step_0']['strategy']}")
    
    if 'votes' in result['results']['step_0']:
        print("\nVotes:")
        for proposal, count in result['results']['step_0']['votes'].items():
            print(f"  - {proposal[:50]}...: {count} votes")
    
    print("\nAll Proposals:")
    for name, proposal in result['results']['step_0']['proposals'].items():
        if "_round_" not in name:  # Show only initial proposals
            print(f"\n{name}:")
            print(f"  {proposal[:200]}...")
            
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure your model provider credentials are correctly configured.")
    print("Run 'konseho setup' for interactive configuration.")