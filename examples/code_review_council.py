#!/usr/bin/env python3
"""Example: Code Review Council with multiple steps."""

import asyncio

from examples.agents import CoderAgent, ExplorerAgent, ReviewerAgent
from konseho import DebateStep, ParallelStep
from konseho.factories import CouncilFactory
from konseho.agents.base import AgentWrapper


async def main():
    """Run a code review council that analyzes, reviews, and improves code."""
    
    # Initialize specialized agents
    explorer = AgentWrapper(ExplorerAgent(), name="CodeExplorer")
    reviewer1 = AgentWrapper(ReviewerAgent(name="SeniorReviewer"), name="SeniorReviewer")
    reviewer2 = AgentWrapper(ReviewerAgent(name="SecurityReviewer"), name="SecurityReviewer")
    coder = AgentWrapper(CoderAgent(), name="RefactoringExpert")
    
    # Create a multi-step council
    factory = CouncilFactory()

    council = factory.create_council(
        name="CodeReviewCouncil",
        steps=[
            # Step 1: Explore the codebase in parallel
            ParallelStep([explorer, reviewer1]),
            
            # Step 2: Debate on findings and priorities
            DebateStep(
        agents=[reviewer1, reviewer2],
                rounds=2,
                voting_strategy="consensus"
            ),
            
            # Step 3: Implement improvements
            ParallelStep([coder])
        ],
        error_strategy="continue"
    )
    
    # Task for the council
    task = """
    Review the authentication module in src/auth.py:
    1. Identify security vulnerabilities
    2. Check code quality and best practices
    3. Suggest and implement improvements
    """
    
    print("🏛️ Code Review Council Starting...")
    print(f"Task: {task}")
    print("-" * 50)
    
    # Execute the council
    result = await council.execute(task)
    
    # Display results
    print("\n📊 Council Results:")
    print(f"Steps completed: {len(result['results'])}")
    
    print("\n🔍 Step 1 - Parallel Analysis:")
    parallel_results = result['results'].get('step_0', {}).get('parallel_results', {})
    for agent, findings in parallel_results.items():
        print(f"\n{agent}:")
        print(findings[:200] + "..." if len(findings) > 200 else findings)
    
    print("\n💬 Step 2 - Review Debate:")
    debate_results = result['results'].get('step_1', {})
    if 'winner' in debate_results:
        print(f"Consensus reached: {debate_results.get('consensus_reached', False)}")
        print(f"Final decision: {debate_results['winner'][:200]}...")
    
    print("\n🔧 Step 3 - Implementation:")
    implementation = result['results'].get('step_2', {}).get('parallel_results', {})
    for agent, code in implementation.items():
        print(f"\n{agent} implementation:")
        print(code[:300] + "..." if len(code) > 300 else code)
    
    print("\n✅ Code Review Council Complete!")
    
    # Show context accumulation
    print("\n📝 Context accumulated:")
    context_summary = council.context.get_summary()
    print(f"Total results stored: {len(context_summary['results'])}")
    print(f"History entries: {context_summary['history_length']}")


if __name__ == "__main__":
    asyncio.run(main())