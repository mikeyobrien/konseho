#!/usr/bin/env python3
"""Main entry point for Konseho CLI."""

import asyncio
import sys
from typing import Optional

from .interface.chat import ChatInterface
from .core.council import Council
from .core.steps import DebateStep
from .agents.base import AgentWrapper


def print_usage():
    """Print usage information."""
    print("""
🏛️  Konseho - Multi-Agent Council Framework

Usage:
    python -m konseho              # Start interactive chat
    python -m konseho --help       # Show this help
    python -m konseho --example    # Run with example agents
    
For custom councils, create a Python script:

    from konseho import Council, DebateStep
    from konseho.agents import AgentWrapper
    
    council = Council([
        DebateStep([agent1, agent2, agent3])
    ])
    
    result = council.run("Your task here")
""")


def create_example_council() -> Council:
    """Create an example council with mock agents."""
    # Import here to avoid circular imports
    from .agents.base import create_agent
    
    # Create mock agents for demo
    explorer = AgentWrapper(create_agent(name="Explorer"), name="Explorer")
    planner = AgentWrapper(create_agent(name="Planner"), name="Planner")  
    coder = AgentWrapper(create_agent(name="Coder"), name="Coder")
    
    return Council(
        name="ExampleCouncil",
        steps=[
            DebateStep(
                agents=[explorer, planner, coder],
                rounds=1,
                voting_strategy="majority"
            )
        ]
    )


async def run_interactive_chat(council: Optional[Council] = None):
    """Run the interactive chat interface."""
    if council is None:
        council = create_example_council()
    
    chat = ChatInterface(use_rich=True)
    
    print("\n💡 Tip: The council will work together to solve your tasks.")
    print("Type 'quit' to exit.\n")
    
    await chat.interactive_session(council)


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print_usage()
        return
    
    if "--example" in args:
        print("🏛️  Starting Konseho with example council...")
        asyncio.run(run_interactive_chat())
    else:
        # Default: start interactive chat
        print("🏛️  Welcome to Konseho Interactive Council")
        print("=" * 50)
        asyncio.run(run_interactive_chat())


if __name__ == "__main__":
    main()
