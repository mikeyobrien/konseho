"""Example demonstrating advanced usage of Council components after refactoring."""

import asyncio
from strands import Agent

from konseho.core import (
    Council,
    DebateStep,
    ParallelStep,
    ErrorHandler,
    ErrorStrategy,
    ModeratorAssigner,
)
from konseho.factories import CouncilFactory, CouncilDependencies
from konseho.core.context import Context
from konseho.execution.events import EventEmitter
from konseho.core.output_manager import OutputManager
from konseho.core.steps import StepResult


async def custom_fallback_handler(error, step, task, context):
    """Custom fallback handler that provides alternative results."""
    print(f"⚠️  Fallback handler invoked for {step.name}: {error}")
    
    return StepResult(
        output=f"Fallback result: Using cached response for '{task}'",
        metadata={
            "fallback": True,
            "original_error": str(error),
            "cached": True,
            "step_name": step.name,
            "agents_involved": []
        }
    )


async def main():
    """Demonstrate advanced Council component usage."""
    
    # Create agents
    researcher = Agent(
        name="researcher",
        model="gpt-4o-mini",
        system_prompt="You are a research expert.",
    )
    
    analyst = Agent(
        name="analyst",
        model="gpt-4o-mini",
        system_prompt="You are a data analyst.",
    )
    
    critic = Agent(
        name="critic",
        model="gpt-4o-mini",
        system_prompt="You are a critical reviewer.",
    )
    
    moderator = Agent(
        name="moderator",
        model="gpt-4o-mini",
        system_prompt="You are a neutral moderator who guides discussions.",
    )
    
    # Example 1: Custom Error Handling
    print("=== Example 1: Custom Error Handling ===")
    
    # Create custom dependencies with error handling
    error_handler = ErrorHandler(
        error_strategy=ErrorStrategy.FALLBACK,
        fallback_handler=custom_fallback_handler
    )
    
    # Create dependencies with custom components
    deps = CouncilDependencies(
        context=Context(),
        event_emitter=EventEmitter(),
        output_manager=OutputManager("custom_error_handling")
    )
    
    # Create council with custom error handler
    council = Council(
        name="error_handling_council",
        steps=[
            ParallelStep([researcher, analyst]),
            DebateStep([researcher, analyst, critic])
        ],
        dependencies=deps,
        error_strategy="fallback"
    )
    
    # Set the custom fallback handler
    council.set_fallback_handler(custom_fallback_handler)
    
    result = await council.execute("Analyze market trends (this might fail)")
    print(f"Result: {result.get('summary', 'No summary')[:200]}...")
    
    # Example 2: Moderator Pool Management
    print("\n=== Example 2: Moderator Pool Management ===")
    
    # Create additional moderators
    senior_mod = Agent(
        name="senior_moderator",
        model="gpt-4o",
        system_prompt="You are a senior moderator with expertise in conflict resolution.",
    )
    
    technical_mod = Agent(
        name="technical_moderator", 
        model="gpt-4o-mini",
        system_prompt="You are a technical moderator for engineering discussions.",
    )
    
    # Create council with multiple debate steps
    factory = CouncilFactory()
    council2 = factory.create_council(
        name="moderated_debates",
        steps=[
            DebateStep([researcher, analyst], name="initial_debate"),
            DebateStep([analyst, critic], name="critical_review"),
            DebateStep([researcher, analyst, critic], name="final_consensus")
        ]
    )
    
    # Set moderator pool - will round-robin through them
    council2.set_moderator_pool([moderator, senior_mod, technical_mod])
    
    result2 = await council2.execute("Design a distributed system architecture")
    print(f"Moderated result: {result2.get('summary', 'No summary')[:200]}...")
    
    # Example 3: Programmatic Step Building
    print("\n=== Example 3: Programmatic Step Building ===")
    
    # Create empty council
    council3 = factory.create_council(name="dynamic_council")
    
    # Add steps programmatically based on conditions
    task_complexity = "high"  # Could be determined dynamically
    
    if task_complexity == "high":
        # Add research phase
        council3.add_step(ParallelStep(
            [researcher, analyst],
            name="research_phase"
        ))
        
        # Add debate with moderator
        debate = DebateStep([researcher, analyst, critic], name="debate_phase")
        council3.add_step(debate)
        
        # Assign specific moderator to this debate
        council3._moderator_assigner.assign_specific_moderator(debate, senior_mod)
        
        # Add synthesis phase
        council3.add_step(ParallelStep(
            [analyst],
            name="synthesis_phase"
        ))
    
    result3 = await council3.execute("Create a comprehensive AI ethics framework")
    print(f"Dynamic council result: {result3.get('summary', 'No summary')[:200]}...")
    
    # Example 4: Event-Driven Monitoring
    print("\n=== Example 4: Event-Driven Monitoring ===")
    
    # Create event emitter with custom handlers
    event_emitter = EventEmitter()
    
    # Add custom event handlers
    step_timings = {}
    
    def on_step_start(data):
        step_name = data.get("step", "unknown")
        step_timings[step_name] = asyncio.get_event_loop().time()
        print(f"⏱️  Step '{step_name}' started")
    
    def on_step_complete(data):
        step_name = data.get("step", "unknown")
        if step_name in step_timings:
            duration = asyncio.get_event_loop().time() - step_timings[step_name]
            print(f"✅ Step '{step_name}' completed in {duration:.2f}s")
    
    event_emitter.on("step_started", on_step_start)
    event_emitter.on("step_completed", on_step_complete)
    
    # Create council with custom event emitter
    deps4 = CouncilDependencies(event_emitter=event_emitter)
    council4 = Council(
        name="monitored_council",
        steps=[
            ParallelStep([researcher, analyst]),
            DebateStep([researcher, analyst, critic])
        ],
        dependencies=deps4
    )
    
    result4 = await council4.execute("Evaluate quantum computing applications")
    print(f"Monitored result: {result4.get('summary', 'No summary')[:200]}...")
    
    # Example 5: Retry Strategy with Max Attempts
    print("\n=== Example 5: Retry Strategy ===")
    
    deps5 = CouncilDependencies()
    council5 = Council(
        name="retry_council",
        steps=[
            ParallelStep([researcher, analyst]),
            DebateStep([researcher, analyst])
        ],
        dependencies=deps5,
        error_strategy="retry",
        max_retries=3
    )
    
    try:
        result5 = await council5.execute("Analyze real-time data streams")
        print(f"Retry result: {result5.get('summary', 'No summary')[:200]}...")
    except Exception as e:
        print(f"Failed after retries: {e}")


if __name__ == "__main__":
    asyncio.run(main())