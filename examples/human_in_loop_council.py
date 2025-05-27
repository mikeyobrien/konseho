#!/usr/bin/env python3
"""Example: Human-in-the-Loop Council for collaborative decision making."""

import asyncio

from examples.agents import CoderAgent, PlannerAgent, ReviewerAgent
from konseho import Council, DebateStep, ParallelStep
from konseho.agents.base import AgentWrapper
from konseho.agents.human import HumanAgent


async def main():
    """Run a council where humans participate alongside AI agents."""
    
    # Initialize agents including human
    human = AgentWrapper(HumanAgent(name="ProductOwner"), name="ProductOwner")
    planner = AgentWrapper(PlannerAgent(), name="TechLead")
    coder1 = AgentWrapper(CoderAgent(name="BackendDev"), name="BackendDev")
    coder2 = AgentWrapper(CoderAgent(name="FrontendDev"), name="FrontendDev")
    reviewer = AgentWrapper(ReviewerAgent(), name="QAEngineer")
    
    # Create a collaborative council
    council = Council(
        name="ProductDevelopmentCouncil",
        steps=[
            # Step 1: Human defines requirements, AI plans
            ParallelStep([human, planner]),
            
            # Step 2: Debate on approach with human input
            DebateStep(
                agents=[human, planner, reviewer],
                rounds=2,
                voting_strategy="moderator",
                moderator=human  # Human has final say
            ),
            
            # Step 3: Parallel implementation
            ParallelStep([coder1, coder2]),
            
            # Step 4: Review with human approval
            DebateStep(
                agents=[reviewer, human],
                rounds=1,
                voting_strategy="consensus"
            )
        ],
        error_strategy="halt"  # Stop on errors for human intervention
    )
    
    # Task for the council
    task = """
    Design and implement a user notification system with the following requirements:
    - Support multiple channels (email, SMS, push notifications)
    - User preferences management
    - Rate limiting and batching
    - Analytics and delivery tracking
    """
    
    print("👥 Human-in-the-Loop Council Starting...")
    print(f"Task: {task}")
    print("-" * 50)
    print("\n🤝 You will be asked to provide input at key decision points.")
    print("Please provide thoughtful responses when prompted.\n")
    
    try:
        # Execute the council
        result = await council.execute(task)
        
        # Display results
        print("\n📊 Council Results:")
        
        print("\n📋 Step 1 - Requirements & Planning:")
        parallel_results = result['results'].get('step_0', {}).get('parallel_results', {})
        for agent, response in parallel_results.items():
            print(f"\n{agent}:")
            print(response[:200] + "..." if len(response) > 200 else response)
        
        print("\n🤔 Step 2 - Approach Decision:")
        debate_results = result['results'].get('step_1', {})
        if 'winner' in debate_results:
            print(f"Decision made by: {debate_results.get('selected_by', 'vote')}")
            print(f"Chosen approach: {debate_results['winner'][:200]}...")
        
        print("\n💻 Step 3 - Implementation:")
        impl_results = result['results'].get('step_2', {}).get('parallel_results', {})
        for agent, code in impl_results.items():
            print(f"\n{agent} implementation:")
            print(code[:200] + "..." if len(code) > 200 else code)
        
        print("\n✅ Step 4 - Review & Approval:")
        review_results = result['results'].get('step_3', {})
        if 'consensus_reached' in review_results:
            print(f"Consensus reached: {review_results['consensus_reached']}")
            print(f"Final approval: {review_results.get('winner', 'Pending')[:200]}...")
        
        print("\n🎉 Product Development Council Complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Council interrupted by user.")
        print("Human intervention is a key feature of this council type!")
    
    except Exception as e:
        print(f"\n❌ Error during council execution: {e}")
        print("Human-in-the-loop councils halt on errors for manual intervention.")


if __name__ == "__main__":
    print("🚀 Starting Human-in-the-Loop Council Example")
    print("=" * 60)
    print("This example demonstrates how humans can participate in councils")
    print("alongside AI agents for collaborative decision making.")
    print("=" * 60)
    
    asyncio.run(main())