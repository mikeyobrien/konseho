#!/usr/bin/env python3
"""Example: Research Council with split work distribution."""

import asyncio

from examples.agents import ExplorerAgent, PlannerAgent
from konseho import Council, DebateStep, SplitStep
from konseho.agents.base import AgentWrapper


async def main():
    """Run a research council that splits complex research across multiple agents."""
    
    # Initialize template agents for splitting
    researcher_template = ExplorerAgent(name="Researcher", temperature=0.7)
    planner = AgentWrapper(PlannerAgent(), name="LeadPlanner")
    
    # Create a council with dynamic work splitting
    council = Council(
        name="ResearchCouncil",
        steps=[
            # Step 1: Split research task across multiple agents
            SplitStep(
                agent_template=researcher_template,
                min_agents=3,
                max_agents=5,
                split_strategy="auto"
            ),
            
            # Step 2: Synthesize findings with debate
            DebateStep(
                agents=[
                    AgentWrapper(PlannerAgent(name="Synthesizer1"), name="Synthesizer1"),
                    AgentWrapper(PlannerAgent(name="Synthesizer2"), name="Synthesizer2"),
                ],
                rounds=1,
                voting_strategy="majority"
            )
        ],
        error_strategy="retry"
    )
    
    # Complex research task
    task = """
    Research and analyze approaches for implementing a distributed cache system:
    1. Evaluate different caching strategies (LRU, LFU, FIFO)
    2. Compare distributed cache solutions (Redis, Hazelcast, Memcached)
    3. Analyze consistency models (eventual, strong, causal)
    4. Review partitioning and sharding strategies
    5. Investigate cache invalidation patterns
    """
    
    print("🔬 Research Council Starting...")
    print(f"Task: {task}")
    print("-" * 50)
    
    # Execute the council
    result = await council.execute(task)
    
    # Display results
    print("\n📊 Council Results:")
    
    print("\n🔍 Step 1 - Split Research:")
    split_results = result['results'].get('step_0', {})
    print(f"Number of researchers: {split_results.get('num_agents', 0)}")
    print(f"Split strategy: {split_results.get('strategy', 'unknown')}")
    
    if 'split_results' in split_results:
        for i, research in enumerate(split_results['split_results']):
            print(f"\nResearcher {i+1} findings:")
            print(research[:200] + "..." if len(research) > 200 else research)
    
    print("\n💬 Step 2 - Synthesis Debate:")
    debate_results = result['results'].get('step_1', {})
    if 'winner' in debate_results:
        print(f"Voting strategy: {debate_results.get('strategy', 'unknown')}")
        print("Final synthesis:")
        print(debate_results['winner'][:300] + "..." if len(debate_results['winner']) > 300 else debate_results['winner'])
    
    print("\n✅ Research Council Complete!")
    
    # Demonstrate context usage
    print("\n📝 Research Context:")
    context_data = council.context.get_summary()
    print(f"Research phases completed: {len(context_data['results'])}")
    
    # Extract key findings
    print("\n🔑 Key Findings Summary:")
    for step_name, step_result in context_data['results'].items():
        print(f"- {step_name}: {type(step_result).__name__}")


if __name__ == "__main__":
    asyncio.run(main())