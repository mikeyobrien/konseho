#!/usr/bin/env python3
"""Interactive chat interface demo for Konseho councils."""

import asyncio

from examples.agents import CoderAgent, ExplorerAgent, PlannerAgent, ReviewerAgent
from konseho import ChatInterface, Council, DebateStep, ParallelStep
from konseho.agents.base import AgentWrapper


async def main():
    """Run the interactive chat interface."""
    
    # Create a versatile council with multiple capabilities
    explorer = AgentWrapper(ExplorerAgent(), name="Explorer")
    planner = AgentWrapper(PlannerAgent(), name="Planner")
    coder = AgentWrapper(CoderAgent(), name="Coder")
    reviewer = AgentWrapper(ReviewerAgent(), name="Reviewer")
    
    # Create a multi-capability council
    council = Council(
        name="InteractiveCouncil",
        steps=[
            # First explore and plan in parallel
            ParallelStep([explorer, planner]),
            
            # Then debate the approach
            DebateStep(
                agents=[planner, coder, reviewer],
                rounds=1,
                voting_strategy="majority"
            ),
            
            # Finally implement
            ParallelStep([coder])
        ],
        error_strategy="continue"
    )
    
    # Create and run the chat interface
    chat = ChatInterface(use_rich=True)
    
    print("🏛️ Konseho Interactive Council")
    print("=" * 50)
    print("This council can help you with:")
    print("- 🔍 Exploring codebases")
    print("- 📋 Planning implementations")
    print("- 💻 Writing code")
    print("- 🔎 Reviewing solutions")
    print("=" * 50)
    print("\nExample tasks you can try:")
    print("- 'Create a REST API endpoint for user registration'")
    print("- 'Review the security of the login function'")
    print("- 'Plan the architecture for a notification system'")
    print("- 'Debug why the search feature is slow'")
    print()
    
    # Run the interactive session
    await chat.interactive_session(council)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSession terminated by user.")