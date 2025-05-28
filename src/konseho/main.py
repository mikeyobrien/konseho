#!/usr/bin/env python3
"""Main entry point for Konseho CLI."""

import asyncio
import logging
import sys

from .agents.base import AgentWrapper
from .core.council import Council
from .core.output_manager import OutputManager
from .core.steps import DebateStep
from .dynamic.builder import DynamicCouncilBuilder
from .interface.chat import ChatInterface

# Configure logging to suppress httpx debug messages
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def print_usage():
    """Print usage information."""
    print(
        """
🏛️  Konseho - Multi-Agent Council Framework

Usage:
    python -m konseho                        # Start interactive chat with default council
    python -m konseho --help                 # Show this help
    python -m konseho --setup                # Run setup wizard (first time)
    python -m konseho --config               # Show current model configuration
    python -m konseho --council balanced     # Use a specific council type
    python -m konseho --dynamic              # Dynamic council based on each query
    python -m konseho -p "your query"        # Run single query (non-interactive)
    python -m konseho --dynamic -p "query"   # Single query with dynamic council
    python -m konseho -p "query" -q          # Single query with minimal output
    python -m konseho --dynamic --analyzer-model claude-3-haiku-20240307  # Specify analyzer model
    python -m konseho --save                 # Save outputs to default directory
    python -m konseho --save --output-dir results  # Save outputs to custom directory
    
Available Councils:
    example      - Basic debate council with Explorer, Planner, and Coder
    balanced     - Well-balanced council for general tasks (default)
    innovation   - Creative brainstorming with Explorer, Visionary, and Critic
    development  - Software development with planning and code review
    research     - Research and analysis with parallel exploration
    dynamic      - Automatically creates agents and steps based on your query
    
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
"""
    )


def create_example_council() -> Council:
    """Create an example council with mock agents."""
    # Import here to avoid circular imports
    from .agents.base import create_agent
    from .factories import CouncilFactory
    from .personas import CODER_PROMPT, EXPLORER_PROMPT, PLANNER_PROMPT

    # Create agents with distinct personas
    explorer = AgentWrapper(
        create_agent(name="Explorer", system_prompt=EXPLORER_PROMPT, temperature=0.8),
        name="Explorer",
    )

    planner = AgentWrapper(
        create_agent(name="Planner", system_prompt=PLANNER_PROMPT, temperature=0.7),
        name="Planner",
    )

    coder = AgentWrapper(
        create_agent(name="Coder", system_prompt=CODER_PROMPT, temperature=0.6),
        name="Coder",
    )

    # Use factory to create council
    factory = CouncilFactory()
    return factory.create_council(
        name="ExampleCouncil",
        steps=[
            DebateStep(
                agents=[explorer, planner, coder], rounds=1, voting_strategy="majority"
            )
        ],
    )


async def run_interactive_chat(
    council: Council | None = None,
    dynamic_mode: bool = False,
    analyzer_model: str | None = None,
    save_outputs: bool = False,
    output_dir: str | None = None,
):
    """Run the interactive chat interface.

    Args:
        council: Pre-built council to use (if not dynamic mode)
        dynamic_mode: Whether to use dynamic council creation
        analyzer_model: Model to use for query analysis in dynamic mode
    """
    if council is None and not dynamic_mode:
        council = create_example_council()

    chat = ChatInterface(
        use_rich=True, save_outputs=save_outputs, output_dir=output_dir
    )

    if dynamic_mode:
        print(
            "\n🧠 Dynamic Council Mode: I'll create specialized agents for each task."
        )
        print("The council composition will be optimized based on your query.")
        if analyzer_model:
            print(f"Using analyzer model: {analyzer_model}")
    else:
        print("\n💡 Tip: The council will work together to solve your tasks.")
    print("Type 'quit' to exit.\n")

    if dynamic_mode:
        # Create a custom chat session for dynamic mode
        await run_dynamic_chat_session(
            chat,
            analyzer_model=analyzer_model,
            save_outputs=save_outputs,
            output_dir=output_dir,
        )
    else:
        await chat.interactive_session(council)


async def run_dynamic_chat_session(
    chat: ChatInterface,
    analyzer_model: str | None = None,
    save_outputs: bool = False,
    output_dir: str | None = None,
):
    """Run chat session with dynamic council creation for each query.

    Args:
        chat: Chat interface to use
        analyzer_model: Model to use for query analysis (defaults to config)
    """
    chat.display_welcome()

    # Dynamic builder with optional analyzer model
    builder = DynamicCouncilBuilder(verbose=True, analyzer_model=analyzer_model)

    while True:
        try:
            # Get user input
            if chat.use_rich:
                task = chat.console.input(
                    "\n[bold cyan]Enter task (or 'quit' to exit):[/bold cyan] "
                )
            else:
                task = input("\nEnter task (or 'quit' to exit): ")

            if task.lower() in ["quit", "exit", "q"]:
                break

            # Create dynamic council for this query
            print("\n🔍 Analyzing your request...")
            council = await builder.build(
                task, save_outputs=save_outputs, output_dir=output_dir
            )

            # Subscribe to council events
            if hasattr(council, "_event_emitter"):
                council._event_emitter.on(
                    "council:start", lambda e, d: chat.display_event(e, d)
                )
                council._event_emitter.on(
                    "step:start", lambda e, d: chat.display_event(e, d)
                )
                council._event_emitter.on(
                    "step:complete", lambda e, d: chat.display_event(e, d)
                )
                council._event_emitter.on(
                    "council:complete", lambda e, d: chat.display_event(e, d)
                )
                council._event_emitter.on(
                    "council:error", lambda e, d: chat.display_event(e, d)
                )

            # Execute council
            result = await council.execute(task)
            chat.display_result(result)

        except KeyboardInterrupt:
            break
        except Exception as e:
            if chat.use_rich:
                chat.console.print(f"[bold red]Error:[/bold red] {e}")
            else:
                print(f"Error: {e}")

    if chat.use_rich:
        chat.console.print("\n[dim]Goodbye![/dim]")
    else:
        print("\nGoodbye!")


async def run_single_query(
    prompt: str,
    council: Council | None = None,
    dynamic_mode: bool = False,
    quiet: bool = False,
    analyzer_model: str | None = None,
    save_outputs: bool = False,
    output_dir: str | None = None,
):
    """Run a single query and exit.

    Args:
        prompt: The query to run
        council: Pre-built council to use (if not dynamic mode)
        dynamic_mode: Whether to use dynamic council creation
        quiet: Whether to suppress verbose output
        analyzer_model: Model to use for query analysis in dynamic mode
    """

    try:
        if dynamic_mode:
            # Create dynamic council for this query
            print("\n🔍 Analyzing your request...")
            builder = DynamicCouncilBuilder(
                verbose=False, analyzer_model=analyzer_model
            )  # Less verbose for single query
            council = await builder.build(
                prompt, save_outputs=save_outputs, output_dir=output_dir
            )

        # For single query mode, we want minimal output
        # Only subscribe to key events
        if hasattr(council, "_event_emitter"):
            # Track progress without showing all details
            def show_progress(event: str, data: dict):
                if event == "council:start":
                    print(f"\n▶ Starting {data.get('council_name', 'Council')}")
                elif event == "step:start":
                    step_type = data.get("step_type", "Step")
                    print(f"→ Executing {step_type}...")
                elif event == "council:error":
                    print(f"❌ Error: {data.get('error', 'Unknown error')}")

            council._event_emitter.on("council:start", show_progress)
            council._event_emitter.on("step:start", show_progress)
            council._event_emitter.on("council:error", show_progress)

        # Execute council
        print(f"\n📋 Task: {prompt}")
        result = await council.execute(prompt)

        # Display final result
        print("\n" + "=" * 50)
        print("📊 Final Result:")
        print("=" * 50)

        # Extract the winner from the last step result
        final_answer = None
        if isinstance(result, dict) and "results" in result:
            step_results = result["results"]
            # Get the last step's result
            last_step_key = (
                sorted([k for k in step_results.keys() if k.startswith("step_")])[-1]
                if step_results
                else None
            )
            if last_step_key:
                step_result = step_results[last_step_key]
                # Handle StepResult objects
                if hasattr(step_result, "output"):
                    final_answer = step_result.output
                # Handle legacy dict format
                elif isinstance(step_result, dict) and "winner" in step_result:
                    final_answer = step_result["winner"]

        if final_answer:
            # Truncate if too long
            display_answer = (
                final_answer[:1000] + "..."
                if len(final_answer) > 1000
                else final_answer
            )
            print(f"\n{display_answer}")
        else:
            print("\n[No final answer produced]")

        # Show execution metadata
        if isinstance(result, dict) and "metadata" in result and result["metadata"]:
            print("\n📈 Summary:")
            for key, value in result["metadata"].items():
                if value:
                    print(f"  • {key}: {value}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


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

    # Parse prompt argument
    prompt = None
    if "-p" in args:
        prompt_index = args.index("-p")
        if prompt_index + 1 < len(args):
            prompt = args[prompt_index + 1]
        else:
            print("❌ Error: -p flag requires a prompt argument")
            print('Usage: konseho -p "your query"')
            return
    elif "--prompt" in args:
        prompt_index = args.index("--prompt")
        if prompt_index + 1 < len(args):
            prompt = args[prompt_index + 1]
        else:
            print("❌ Error: --prompt flag requires a prompt argument")
            print('Usage: konseho --prompt "your query"')
            return

    # Check for quiet mode (less verbose output)
    quiet_mode = "-q" in args or "--quiet" in args

    # Check for output saving options
    save_outputs = "--save" in args or "-s" in args
    output_dir = None
    if "--output-dir" in args:
        dir_index = args.index("--output-dir")
        if dir_index + 1 < len(args):
            output_dir = args[dir_index + 1]
        else:
            print("❌ Error: --output-dir requires a directory argument")
            return

    # Validate prompt if provided
    if prompt is not None and not prompt.strip():
        print("❌ Error: Prompt cannot be empty")
        print('Usage: konseho -p "your query"')
        return

    # Check environment setup first
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

    # Handle council selection
    council_type = "balanced"  # default
    council = None
    dynamic_mode = False
    analyzer_model = None

    # Check for analyzer model argument
    if "--analyzer-model" in args:
        model_index = args.index("--analyzer-model")
        if model_index + 1 < len(args):
            analyzer_model = args[model_index + 1]
        else:
            print("❌ Error: --analyzer-model requires a model name argument")
            print("Usage: konseho --dynamic --analyzer-model claude-3-haiku-20240307")
            return

    # Check for dynamic mode first
    if "--dynamic" in args:
        dynamic_mode = True
        council_type = "dynamic"
    elif "--council" in args:
        council_index = args.index("--council")
        if council_index + 1 < len(args):
            council_type = args[council_index + 1].lower()
            if council_type == "dynamic":
                dynamic_mode = True
    elif "--example" in args:
        council_type = "example"

    # Create the appropriate council
    if not prompt:
        # Interactive mode
        print("🏛️  Welcome to Konseho Interactive Council")
        print("=" * 50)

    if dynamic_mode:
        if prompt:
            # Non-interactive dynamic mode
            print("🏛️  Konseho - Dynamic Council Mode")
            print("=" * 50)
            asyncio.run(
                run_single_query(
                    prompt,
                    council=None,
                    dynamic_mode=True,
                    quiet=quiet_mode,
                    analyzer_model=analyzer_model,
                    save_outputs=save_outputs,
                    output_dir=output_dir,
                )
            )
        else:
            print("Using dynamic council mode...")
            # Start the chat with dynamic mode
            asyncio.run(
                run_interactive_chat(
                    council=None,
                    dynamic_mode=True,
                    analyzer_model=analyzer_model,
                    save_outputs=save_outputs,
                    output_dir=output_dir,
                )
            )
    elif council_type == "example":
        council = create_example_council()
        # Set output saving if requested
        if save_outputs:
            council.save_outputs = True
            council.output_manager = OutputManager(output_dir or "council_outputs")
        if prompt:
            # Non-interactive mode
            print("🏛️  Konseho - Example Council")
            print("=" * 50)
            asyncio.run(run_single_query(prompt, council, quiet=quiet_mode))
        else:
            print(f"Using {council_type} council...")
            asyncio.run(run_interactive_chat(council))
    else:
        try:
            from .example_councils import COUNCILS

            if council_type in COUNCILS:
                council = COUNCILS[council_type]()
                if prompt:
                    # Non-interactive mode
                    print(f"🏛️  Konseho - {council_type.capitalize()} Council")
                    print("=" * 50)
                    asyncio.run(run_single_query(prompt, council, quiet=quiet_mode))
                else:
                    print(f"Using {council_type} council...")
                    asyncio.run(run_interactive_chat(council))
            else:
                print(f"⚠️  Unknown council type: {council_type}")
                print(
                    "Available councils: example, balanced, innovation, development, research, dynamic"
                )
                print("Falling back to balanced council...")
                council = COUNCILS["balanced"]()
                if prompt:
                    asyncio.run(run_single_query(prompt, council, quiet=quiet_mode))
                else:
                    asyncio.run(run_interactive_chat(council))
        except Exception as e:
            print(f"❌ Error creating {council_type} council: {e}")
            print("Falling back to example council...")
            council = create_example_council()
            if prompt:
                asyncio.run(run_single_query(prompt, council, quiet=quiet_mode))
            else:
                asyncio.run(run_interactive_chat(council))


if __name__ == "__main__":
    main()
