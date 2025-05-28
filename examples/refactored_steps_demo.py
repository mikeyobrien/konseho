"""Example demonstrating the refactored step architecture.

This example shows how the new simplified step structure makes it easy
to create and compose different coordination patterns while following
SOLID principles.
"""

import asyncio
from strands import Agent

from konseho.agents.base import AgentWrapper
from konseho.core.context import Context
from konseho.core.step_factory import StepFactory
from konseho.core.steps_v2 import DebateConfig, DebateStep, ParallelStep
from konseho.core.debate_components import WeightedVoting
from konseho.core.parallel_strategies import (
    DomainParallelStrategy,
    TaskSplitStrategy,
    LoadBalancedStrategy,
)


async def simple_debate_example():
    """Example 1: Simple debate with default settings."""
    print("\n=== Simple Debate Example ===")

    # Create agents
    agents = [
        AgentWrapper(Agent(name="optimist", model="gpt-4o-mini")),
        AgentWrapper(Agent(name="pessimist", model="gpt-4o-mini")),
        AgentWrapper(Agent(name="realist", model="gpt-4o-mini")),
    ]

    # Create debate step using factory - simple one-liner!
    step = StepFactory.debate(agents)

    # Execute
    context = Context()
    result = await step.execute(
        "Should we rewrite our monolithic app as microservices?", context
    )

    print(f"Winner: {result.output[:100]}...")
    print(f"Votes: {result.metadata['vote_details']['votes']}")


async def weighted_debate_example():
    """Example 2: Weighted voting based on expertise."""
    print("\n=== Weighted Debate Example ===")

    # Create agents with different expertise levels
    senior = AgentWrapper(Agent(name="senior_dev", model="gpt-4o"))
    junior1 = AgentWrapper(Agent(name="junior_dev_1", model="gpt-4o-mini"))
    junior2 = AgentWrapper(Agent(name="junior_dev_2", model="gpt-4o-mini"))

    # Define weights based on experience
    weights = {
        "senior_dev": 2.0,
        "junior_dev_1": 0.75,
        "junior_dev_2": 0.75,
    }

    # Create weighted debate
    step = StepFactory.weighted_debate([senior, junior1, junior2], weights)

    # Execute
    context = Context()
    result = await step.execute(
        "What testing strategy should we adopt for our API?", context
    )

    print(f"Winner: {result.output[:100]}...")
    print(f"Weighted scores: {result.metadata['vote_details']['weighted_scores']}")


async def domain_parallel_example():
    """Example 3: Parallel analysis from different perspectives."""
    print("\n=== Domain Parallel Example ===")

    # Create domain expert agents
    agents = [
        AgentWrapper(Agent(name="security_expert", model="gpt-4o")),
        AgentWrapper(Agent(name="performance_expert", model="gpt-4o")),
        AgentWrapper(Agent(name="ux_expert", model="gpt-4o")),
    ]

    # Create parallel step with custom domains
    step = StepFactory.domain_parallel(
        agents, domains=["security", "performance", "user experience"]
    )

    # Execute
    context = Context()
    result = await step.execute("Review our authentication system design", context)

    print("Combined analysis:")
    print(result.output)


async def custom_strategy_example():
    """Example 4: Custom parallel strategy."""
    print("\n=== Custom Strategy Example ===")

    # Create agents
    agents = [
        AgentWrapper(Agent(name="agent1", model="gpt-4o-mini")),
        AgentWrapper(Agent(name="agent2", model="gpt-4o-mini")),
    ]

    # Use task splitting strategy
    step = StepFactory.task_split(agents, split_method="by_lines")

    # Execute with multi-line task
    context = Context()
    result = await step.execute(
        "1. Analyze the database schema\n"
        "2. Review the API endpoints\n"
        "3. Check the authentication flow\n"
        "4. Evaluate the caching strategy",
        context,
    )

    print("Task split results:")
    for subtask, result in result.metadata["individual_results"].items():
        print(f"\n{subtask}: {result[:100]}...")


async def composed_council_example():
    """Example 5: Combining multiple steps."""
    print("\n=== Composed Council Example ===")

    # Create agents
    agents = [
        AgentWrapper(Agent(name="analyst1", model="gpt-4o")),
        AgentWrapper(Agent(name="analyst2", model="gpt-4o")),
        AgentWrapper(Agent(name="analyst3", model="gpt-4o")),
    ]

    # Step 1: Parallel domain analysis
    parallel_step = StepFactory.domain_parallel(
        agents, domains=["technical", "business", "risk"]
    )

    # Step 2: Debate the findings
    debate_step = StepFactory.consensus_debate(agents, max_rounds=3)

    # Execute both steps
    context = Context()

    # First, gather perspectives
    parallel_result = await parallel_step.execute(
        "Should we migrate to Kubernetes?", context
    )

    # Add findings to context
    context.add("domain_analyses", parallel_result.output)

    # Then debate based on the analyses
    debate_result = await debate_step.execute(
        f"Based on these analyses, what's our recommendation?\n\n{parallel_result.output}",
        context,
    )

    print(f"Final recommendation: {debate_result.output[:200]}...")


async def main():
    """Run all examples."""
    # Run examples sequentially to avoid rate limits
    await simple_debate_example()
    await asyncio.sleep(2)

    await weighted_debate_example()
    await asyncio.sleep(2)

    await domain_parallel_example()
    await asyncio.sleep(2)

    await custom_strategy_example()
    await asyncio.sleep(2)

    await composed_council_example()


if __name__ == "__main__":
    asyncio.run(main())

