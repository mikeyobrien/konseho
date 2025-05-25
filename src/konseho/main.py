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
    python -m konseho --setup      # Run setup wizard (first time)
    python -m konseho --config     # Show current model configuration
    python -m konseho --example    # Run with example agents
    
Model Provider Setup:
    1. Copy .env.example to .env
    2. Set DEFAULT_PROVIDER (anthropic, openai, bedrock, ollama)
    3. Add your API keys
    4. Install provider: pip install strands-agents[provider]
    
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
    
    if "--setup" in args:
        from .setup_wizard import run_setup_wizard
        run_setup_wizard()
        return
    
    if "--config" in args:
        from .config import print_config_info
        print("\n📋 Current Model Configuration:")
        print("-" * 30)
        print_config_info()
        print("\nTo change configuration, edit your .env file.")
        return
    
    if "--example" in args:
        print("🏛️  Starting Konseho with example council...")
        asyncio.run(run_interactive_chat())
    else:
        # Default: start interactive chat
        print("🏛️  Welcome to Konseho Interactive Council")
        print("=" * 50)
        
        # Check if this is first run
        import os
        if not os.path.exists(".env"):
            print("\n🆕 First time using Konseho?")
            print("   Run setup wizard: python -m konseho --setup")
            print("   Or copy .env.example to .env and add your API keys\n")
        else:
            # Check if model is configured
            try:
                from .config import get_model_config
                config = get_model_config()
                if config.provider in ["anthropic", "openai"] and not config.api_key:
                    print("\n⚠️  Warning: No API key found for", config.provider)
                    print("   Run: python -m konseho --setup")
                    print("   Or edit .env to add your API key\n")
            except Exception:
                pass
            
        asyncio.run(run_interactive_chat())


if __name__ == "__main__":
    main()
